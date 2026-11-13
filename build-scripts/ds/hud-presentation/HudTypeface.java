package com.cleverraven.cataclysmdda;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.AssetManager;
import android.graphics.Typeface;
import android.graphics.fonts.Font;
import android.graphics.fonts.FontFamily;
import android.os.Build;
import android.util.Log;

import java.io.IOException;

/** One font selection per Presentation, using fonts already shipped with CDDA. */
final class HudTypeface {
    private static final String TAG = "CDDA-DS-FONT";
    static final String PRIMARY = "data/font/Terminus.ttf";
    static final String FALLBACK = "data/font/unifont.ttf";
    final Typeface typeface;
    final String description;

    private HudTypeface(Typeface typeface, String description) {
        this.typeface = typeface;
        this.description = description;
    }

    static HudTypeface load(Context context) {
        AssetManager assets = context.getAssets();
        if (Build.VERSION.SDK_INT >= 29) {
            try {
                return Api29.load(assets);
            } catch (IOException | RuntimeException error) {
                Log.w(TAG, "Custom font chain unavailable; trying legacy Terminus loading", error);
            }
        }
        try {
            return new HudTypeface(Typeface.createFromAsset(assets, PRIMARY),
                "Terminus (system glyph fallback)");
        } catch (RuntimeException error) {
            // A font problem must not prevent the read-only HUD from appearing.
            // Report the fallback both in the Android log and the HUD footer.
            Log.w(TAG, "Terminus unavailable; using Android monospace", error);
            return new HudTypeface(Typeface.MONOSPACE, "Android monospace (font fallback)");
        }
    }

    // Isolate APIs unavailable on Android 7-9 (the APK's existing minimum is 24).
    @TargetApi(29)
    private static final class Api29 {
        static HudTypeface load(AssetManager assets) throws IOException {
            Font primary = new Font.Builder(assets, PRIMARY).build();
            Typeface.CustomFallbackBuilder builder = new Typeface.CustomFallbackBuilder(
                new FontFamily.Builder(primary).build());
            String description = "Terminus + Unifont";
            try {
                Font fallback = new Font.Builder(assets, FALLBACK).build();
                builder.addCustomFallback(new FontFamily.Builder(fallback).build());
            } catch (IOException | RuntimeException error) {
                Log.w(TAG, "Unifont unavailable; retaining Terminus with system glyph fallback", error);
                description = "Terminus (system glyph fallback)";
            }
            Typeface result = builder.setStyle(primary.getStyle())
                .setSystemFallback("monospace").build();
            return new HudTypeface(result, description);
        }
    }
}
