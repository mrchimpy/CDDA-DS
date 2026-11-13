package com.cleverraven.cataclysmdda;

import android.content.res.ColorStateList;
import android.graphics.PorterDuff;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.BackgroundColorSpan;
import android.text.style.ForegroundColorSpan;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Immutable native presentation copy. No Java gameplay thresholds or palette guesses. */
final class NativeHudColors {
    private static final int SCALARS = 20, WIDGETS = 29, MAX_RUNS = 4096;
    private static final int MAX_WORDS = 50 + WIDGETS * (1 + 4 * MAX_RUNS);
    private static final int GRAY = 0xff969696, BLACK = 0xff000000, TRACK = 0xff636363;
    private static final String[] BODY_NAMES = {"Head", "Torso", "Left arm", "Right arm", "Left leg", "Right leg"};
    final boolean valid, complete;
    private final Ink neutral;
    private final int track;
    private final Ink[] scalar;
    private final Run[][] widgets;

    private static final class Ink {
        final int fg, bg;
        Ink(int fg, int bg) { this.fg = fg; this.bg = bg; }
    }
    private static final class Run {
        final int start, end;
        final Ink ink;
        Run(int start, int end, Ink ink) { this.start = start; this.end = end; this.ink = ink; }
    }
    private NativeHudColors(boolean valid, boolean complete, Ink neutral, int track,
            Ink[] scalar, Run[][] widgets) {
        this.valid = valid; this.complete = complete; this.neutral = neutral;
        this.track = track; this.scalar = scalar; this.widgets = widgets;
    }
    private static NativeHudColors fallback() {
        Ink neutral = new Ink(GRAY, BLACK);
        Ink[] scalars = new Ink[SCALARS]; Arrays.fill(scalars, neutral);
        Run[][] runs = new Run[WIDGETS][];
        for (int i = 0; i < WIDGETS; i++) runs[i] = new Run[0];
        return new NativeHudColors(false, false, neutral, TRACK, scalars, runs);
    }

    // Keep accepted value decoders unchanged. A malformed color extension must not
    // corrupt otherwise valid readings; it falls back visibly to neutral styling.
    static Object[] values(Object[] raw) {
        return raw != null && (raw.length == 2 || raw.length == 3)
            ? new Object[] {raw[0], raw[1]} : null;
    }
    private static int color(long word) {
        if (word < 0 || word > 0xffffffffL || (word >>> 24) != 255) throw new IllegalArgumentException();
        return (int) word;
    }
    private static int bounded(long word, int maximum) {
        if (word < 0 || word > maximum) throw new IllegalArgumentException();
        return (int) word;
    }
    private static final class Cursor {
        final long[] data; int pos;
        Cursor(long[] data) { this.data = data.clone(); }
        long next() { if (pos >= data.length) throw new IllegalArgumentException(); return data[pos++]; }
        Ink ink() { return new Ink(color(next()), color(next())); }
    }

    // Byte boundaries to UTF-16 boundaries. Emoji/supplementary characters take
    // two Java chars, never two UTF-8 bytes. Reject ranges splitting a code point.
    private static int[] boundaries(String text, byte[] encoded) {
        if (encoded.length > 65536 || !Arrays.equals(text.getBytes(StandardCharsets.UTF_8), encoded))
            throw new IllegalArgumentException();
        int[] map = new int[encoded.length + 1]; Arrays.fill(map, -1);
        int bytes = 0;
        for (int chars = 0; chars < text.length();) {
            map[bytes] = chars;
            int cp = text.codePointAt(chars);
            bytes += cp <= 0x7f ? 1 : cp <= 0x7ff ? 2 : cp <= 0xffff ? 3 : 4;
            chars += Character.charCount(cp);
        }
        if (bytes != encoded.length) throw new IllegalArgumentException();
        map[bytes] = text.length();
        return map;
    }

    static NativeHudColors decode(Object[] raw, ActivityHudSnapshot activity) {
        try {
            if (activity == null || !activity.core.ready || raw == null || raw.length != 3
                    || !(raw[2] instanceof long[]) || !(raw[1] instanceof byte[][])) return fallback();
            long[] words = (long[]) raw[2];
            if (words.length < 79 || words.length > MAX_WORDS) return fallback();
            Cursor in = new Cursor(words);
            if (in.next() != 0x44534331L || in.next() != 1
                    || in.next() != activity.core.sequence || in.next() != 1) return fallback();
            boolean complete = bounded(in.next(), 1) == 1;
            Ink neutral = in.ink(); int track = color(in.next());
            if (in.next() != SCALARS) return fallback();
            Ink[] scalar = new Ink[SCALARS];
            for (int i = 0; i < SCALARS; i++) scalar[i] = in.ink();
            if (in.next() != WIDGETS) return fallback();
            byte[][] texts = (byte[][]) raw[1];
            if (texts.length != WIDGETS + 1) return fallback();
            Run[][] widgets = new Run[WIDGETS][];
            for (int i = 0; i < WIDGETS; i++) {
                int count = bounded(in.next(), MAX_RUNS);
                widgets[i] = new Run[count];
                if (count == 0) continue;
                if (!activity.available(i)) return fallback();
                if (texts[i + 1] == null) return fallback();
                byte[] encoded = texts[i + 1].clone();
                int[] map = boundaries(activity.text(i), encoded);
                int previous = 0;
                for (int j = 0; j < count; j++) {
                    int start = bounded(in.next(), encoded.length);
                    int end = bounded(in.next(), encoded.length);
                    Ink ink = in.ink();
                    if (start != previous || end <= start || map[start] < 0 || map[end] < 0)
                        return fallback();
                    widgets[i][j] = new Run(map[start], map[end], ink); previous = end;
                }
                if (previous != encoded.length) return fallback();
            }
            if (in.pos != words.length) return fallback();
            return new NativeHudColors(true, complete, neutral, track, scalar, widgets);
        } catch (IllegalArgumentException | IndexOutOfBoundsException | ClassCastException error) {
            return fallback();
        }
    }

    private static void span(SpannableString text, int start, int end, Ink ink) {
        if (end <= start) return;
        text.setSpan(new ForegroundColorSpan(ink.fg), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        text.setSpan(new BackgroundColorSpan(ink.bg), start, end, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
    }
    private void set(TextView view, SpannableString text) {
        view.setTextColor(neutral.fg);
        view.setText(text); // New text replaces old foreground AND background spans.
    }
    void scalar(TextView view, String text, int valueStart, int index) {
        SpannableString out = new SpannableString(text);
        span(out, 0, valueStart, neutral);
        span(out, valueStart, text.length(), scalar[index]);
        set(view, out);
    }
    void bodyLabel(TextView view, int part) { scalar(view, BODY_NAMES[part], 0, 7 + part); }
    void widget(TextView view, ActivityHudSnapshot activity, int field) {
        String full = activity.label(field), value = activity.text(field);
        SpannableString out = new SpannableString(full);
        if (!activity.available(field) || value.trim().isEmpty() || widgets[field].length == 0) {
            span(out, 0, full.length(), neutral);
        } else {
            int prefix = full.length() - value.length();
            span(out, 0, prefix, neutral);
            for (Run run : widgets[field]) span(out, prefix + run.start, prefix + run.end, run.ink);
        }
        set(view, out);
    }
    void bar(ProgressBar bar, int index, boolean empty) {
        bar.setProgressTintMode(PorterDuff.Mode.SRC_IN);
        bar.setProgressBackgroundTintMode(PorterDuff.Mode.SRC_IN);
        bar.setProgressTintList(ColorStateList.valueOf(scalar[index].fg));
        // At exact zero, preserve a visible native warning color on the empty
        // track, analogous to the native colored empty graph symbols. No fake HP.
        bar.setProgressBackgroundTintList(ColorStateList.valueOf(empty ? scalar[index].fg : track));
    }
    static void reset(TextView[] labels, ProgressBar[] bars, ProgressBar stamina, TextView value) {
        NativeHudColors colors = fallback();
        value.setTextColor(GRAY);
        for (int i = 0; i < labels.length; i++) {
            labels[i].setText(BODY_NAMES[i]); labels[i].setTextColor(GRAY);
            colors.bar(bars[i], i + 1, false);
        }
        colors.bar(stamina, 0, false);
    }
    String diagnostic() {
        return !valid ? "\nNative colors unavailable; neutral fallback"
            : !complete ? "\nSome native colors unavailable" : "";
    }
}
