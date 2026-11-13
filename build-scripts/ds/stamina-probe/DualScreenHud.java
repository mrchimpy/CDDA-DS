package com.cleverraven.cataclysmdda;

import android.app.Activity;
import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.hardware.display.DisplayManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Experimental one-value HUD. No input injection or game actions. */
final class DualScreenHud implements DisplayManager.DisplayListener {
    private static final String TAG = "CDDA-DS-HUD";
    private final Activity activity;
    private final DisplayManager displays;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private HudPresentation panel;
    private boolean resumed;
    private boolean registered;
    private boolean noticeShown;

    DualScreenHud(Activity activity) {
        this.activity = activity;
        displays = (DisplayManager) activity.getSystemService(Context.DISPLAY_SERVICE);
    }

    // Native code returns a copy: active, ready, current, maximum, sequence, age_ms.
    private static native long[] nativeSnapshot();

    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            if (!resumed || panel == null || !panel.isShowing()) return;
            try {
                panel.render(nativeSnapshot());
            } catch (UnsatisfiedLinkError error) {
                panel.setMessage("Waiting for the game engine");
            } catch (RuntimeException error) {
                Log.e(TAG, "Snapshot read failed", error);
                panel.setMessage("Snapshot unavailable - see Android log");
            }
            if (resumed && panel != null) handler.postDelayed(this, 250);
        }
    };

    void start() {
        if (resumed) return;
        resumed = true;
        if (displays != null) {
            displays.registerDisplayListener(this, handler);
            registered = true;
        }
        selectDisplay();
    }

    void stop() {
        resumed = false;
        handler.removeCallbacks(refresh);
        if (registered) {
            displays.unregisterDisplayListener(this);
            registered = false;
        }
        dismissPanel();
    }

    private void dismissPanel() {
        HudPresentation old = panel;
        panel = null;
        if (old != null) {
            try {
                old.dismiss();
            } catch (RuntimeException error) {
                Log.w(TAG, "Secondary window was already unavailable", error);
            }
        }
    }

    private void selectDisplay() {
        if (!resumed || displays == null || activity.isFinishing()) return;
        Display main = activity.getWindow().getDecorView().getDisplay();
        if (main == null) main = activity.getWindowManager().getDefaultDisplay();
        final int mainId = main.getDisplayId();
        StringBuilder details = new StringBuilder("Stamina probe; main display=" + mainId + "\n");
        for (Display display : displays.getDisplays()) {
            details.append("id=").append(display.getDisplayId())
                .append(" name=").append(display.getName())
                .append(" flags=").append(display.getFlags())
                .append(" state=").append(display.getState()).append('\n');
        }
        Display candidate = null;
        int candidates = 0;
        for (Display display : displays.getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION)) {
            if (display.getDisplayId() != mainId && display.isValid()
                    && display.getState() != Display.STATE_OFF) {
                candidate = display;
                candidates++;
            }
        }
        details.append("Eligible secondary displays=").append(candidates).append('\n');
        if (candidates != 1) {
            dismissPanel();
            String reason = candidates == 0 ? "No presentation display is available"
                : "Multiple secondary displays - disconnect extras for this probe";
            report(details.toString() + reason);
            notifyOnce(reason);
            return;
        }
        if (panel != null && panel.isShowing()
                && panel.getDisplay().getDisplayId() == candidate.getDisplayId()) return;
        dismissPanel();
        try {
            final HudPresentation next = new HudPresentation(activity, candidate);
            next.setOnDismissListener(dialog -> {
                if (panel == next) {
                    panel = null;
                    handler.removeCallbacks(refresh);
                }
            });
            panel = next;
            next.show();
            report(details.toString() + "Showing on display=" + candidate.getDisplayId());
            handler.removeCallbacks(refresh);
            handler.post(refresh);
        } catch (RuntimeException error) {
            // InvalidDisplayException/BadTokenException/SecurityException: fail back
            // to the intact original sidebar; never replace or pause the engine.
            dismissPanel();
            report(details.toString() + "Presentation failed: " + error);
            Log.e(TAG, "Cannot show secondary HUD", error);
            notifyOnce("Lower HUD unavailable; original sidebar remains active");
        }
    }

    private void notifyOnce(String message) {
        if (!noticeShown) {
            Toast.makeText(activity, "CDDA-DS: " + message, Toast.LENGTH_LONG).show();
            noticeShown = true;
        }
    }

    private void report(String message) {
        Log.i(TAG, message);
        File directory = activity.getExternalFilesDir(null);
        if (directory == null) return;
        try (FileOutputStream stream = new FileOutputStream(
                new File(directory, "ds-hud-probe.txt"), false)) {
            stream.write(message.getBytes(StandardCharsets.UTF_8));
        } catch (Exception error) {
            Log.w(TAG, "Could not write display diagnostic", error);
        }
    }

    @Override public void onDisplayAdded(int id) { selectDisplay(); }
    @Override public void onDisplayRemoved(int id) { selectDisplay(); }
    @Override public void onDisplayChanged(int id) { selectDisplay(); }

    private static final class HudPresentation extends Presentation {
        private TextView value;
        private TextView status;
        private ProgressBar bar;

        HudPresentation(Context context, Display display) {
            super(context, display, android.R.style.Theme_Material_NoActionBar);
            Window window = getWindow();
            if (window != null) {
                // Do not request keyboard/gamepad focus. Touches are consumed by
                // the read-only view rather than passed to the launcher beneath.
                window.addFlags(WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE);
                window.clearFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            }
            setCancelable(false);
        }

        @Override protected void onCreate(Bundle state) {
            super.onCreate(state);
            LinearLayout layout = new LinearLayout(getContext());
            layout.setOrientation(LinearLayout.VERTICAL);
            layout.setGravity(Gravity.CENTER_VERTICAL);
            int padding = Math.round(24 * getContext().getResources().getDisplayMetrics().density);
            layout.setPadding(padding, padding, padding, padding);
            layout.setBackgroundColor(Color.rgb(18, 22, 27));
            layout.setFocusable(false);
            layout.setOnTouchListener((view, event) -> true);
            TextView title = text("CDDA-DS / STAMINA PROBE", 22);
            value = text("Waiting for a game", 34);
            status = text("Read-only. The original sidebar remains above.", 16);
            bar = new ProgressBar(getContext(), null, android.R.attr.progressBarStyleHorizontal);
            bar.setMax(1000);
            layout.addView(title);
            layout.addView(value);
            layout.addView(bar, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
            layout.addView(status);
            setContentView(layout);
            Window window = getWindow();
            if (window != null) {
                window.setLayout(WindowManager.LayoutParams.MATCH_PARENT,
                                 WindowManager.LayoutParams.MATCH_PARENT);
            }
        }

        private TextView text(String content, int size) {
            TextView view = new TextView(getContext());
            view.setText(content);
            view.setTextSize(size);
            view.setTextColor(Color.WHITE);
            view.setPadding(0, 8, 0, 8);
            view.setFocusable(false);
            return view;
        }

        void setMessage(String message) {
            value.setText(message);
            bar.setProgress(0);
            status.setText("Read-only diagnostic; original game interface is unchanged.");
        }

        void render(long[] state) {
            if (state == null || state.length != 6) {
                setMessage("Snapshot unavailable");
                return;
            }
            if (state[0] == 0) {
                setMessage("No active game");
                return;
            }
            if (state[1] == 0 || state[3] <= 0) {
                setMessage("Waiting for the first game redraw");
                return;
            }
            double percent = 100.0 * state[2] / state[3];
            value.setText(String.format(Locale.ROOT, "Stamina: %.1f%%\n%d / %d",
                                       percent, state[2], state[3]));
            bar.setProgress((int) Math.max(0, Math.min(1000, percent * 10)));
            status.setText(String.format(Locale.ROOT,
                "Snapshot %d | last game redraw %.1f s ago\n"
                + "Menus and turn waiting may leave this snapshot unchanged.\n"
                + "Read-only: no game actions, no turn advancement.", state[4], state[5] / 1000.0));
        }
    }
}
