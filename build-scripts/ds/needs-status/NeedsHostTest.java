package com.cleverraven.cataclysmdda;

import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Display;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.ScrollView;
import android.widget.TextView;
import java.lang.reflect.*;
import java.util.*;

/** Real native JNI and production Java; Android calls use host substitutes only. */
public final class NeedsHostTest {
    private static native void seed(int mode);
    static void check(boolean value, String why) { if (!value) throw new AssertionError(why); }
    static Object field(Object o, String name) throws Exception {
        Field f = o.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(o);
    }
    static void invoke(Object o, String name, Class<?> type, Object value) throws Exception {
        Method m = o.getClass().getDeclaredMethod(name, type); m.setAccessible(true); m.invoke(o, value);
    }
    static Object[] snapshot() throws Exception {
        Method m = DualScreenHud.class.getDeclaredMethod("nativeSnapshot"); m.setAccessible(true);
        return (Object[]) m.invoke(null);
    }
    static List<TextView> texts(View v) {
        List<TextView> result = new ArrayList<>();
        if (v instanceof TextView) result.add((TextView) v);
        if (v instanceof ViewGroup) for (View child : ((ViewGroup) v).children) result.addAll(texts(child));
        return result;
    }
    static void common(Presentation p, TextView[] rows, HudTypeface font) {
        check(texts(p.content).size() == 36, "three additions, nine removals; no spacer views");
        check(rows.length == 29, "all wire slots retained and appended");
        for (int i = 0; i < rows.length; i++) {
            check((rows[i] == null) == (i >= 5 && i <= 13), "only selected nine absent: " + i);
            if (rows[i] != null) check(rows[i].size == 16f, "readout size unchanged");
        }
        check(p.window.background.color == Color.BLACK && p.content.background == Color.BLACK,
            "black window and viewport");
        check(((ViewGroup) p.content).children.get(0).background == Color.BLACK, "black content");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE) != 0, "focus flag");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_DIM_BEHIND) == 0, "no dim");
        check(!p.content.focusable && ((ScrollView) p.content).fill, "scroll calls unchanged");
        check(((ViewGroup) p.content).descendants == ViewGroup.FOCUS_BLOCK_DESCENDANTS, "descendant block");
        for (TextView t : texts(p.content)) {
            check(t.face == font.typeface && t.color == Color.WHITE && !t.focusable, "shared presentation");
            check(t.spacing == 0f && t.features.equals("'liga' 0, 'clig' 0, 'kern' 0"), "shaping retained");
        }
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]); String scenario = args[1];
        Context context = new Context();
        if (scenario.equals("fallback")) context.assets.failPrimary = true;
        Class<?> c = Class.forName("com.cleverraven.cataclysmdda.DualScreenHud$HudPresentation");
        Constructor<?> ctor = c.getDeclaredConstructor(Context.class, Display.class); ctor.setAccessible(true);
        Presentation p = (Presentation) ctor.newInstance(context, new Display());
        invoke(p, "onCreate", Bundle.class, new Bundle());
        TextView[] rows = (TextView[]) field(p, "activityValues");
        HudTypeface font = (HudTypeface) field(p, "hudFont");
        common(p, rows, font);
        check(font.description.equals(scenario.equals("fallback")
            ? "Android monospace (font fallback)" : "Terminus + Unifont"), "font diagnostic retained");
        int fontCalls = context.assets.modernCalls + context.assets.legacyCalls;
        seed(2); Object[] raw = snapshot();
        check(((long[]) raw[0]).length == 53 && ((byte[][]) raw[1]).length == 30, "native wire shape");
        ActivityHudSnapshot decoded = ActivityHudSnapshot.decode(raw);
        check(decoded != null && decoded.core.coreLabel(5).equals("Focus: 125"), "core preserved");
        for (int i = 0; i < 26; i++) check(decoded.text(i).equals("field " + i), "prior wire field " + i);
        invoke(p, "render", Object[].class, raw);
        check(rows[26].text.equals("Hunger: Satisfied") && rows[27].text.equals("Thirst: Slaked")
            && rows[28].text.equals("Rest: Tired"), "three native descriptions");
        check(rows[17].text.equals("Body comfort: field 17") && rows[25].text.equals("Worn feet: field 25"),
            "retained body/clothing rows");
        check(((TextView) field(p, "value")).size == 22f, "stamina size unchanged");
        if (scenario.equals("changed")) {
            seed(3); invoke(p, "render", Object[].class, snapshot());
            check(rows[26].text.equals("Hunger: Hungry") && rows[27].text.equals("Thirst: Very thirsty")
                && rows[28].text.equals("Rest: Dead Tired"), "changed descriptions");
        } else if (scenario.equals("blank") || scenario.equals("whitespace") || scenario.equals("missing")) {
            seed(scenario.equals("blank") ? 4 : scenario.equals("whitespace") ? 7 : 5);
            invoke(p, "render", Object[].class, snapshot());
            String suffix = scenario.equals("missing") ? "Unavailable" : "\u2014";
            check(rows[26].text.equals("Hunger: " + suffix) && rows[27].text.equals("Thirst: " + suffix)
                && rows[28].text.equals("Rest: " + suffix), "blank/missing distinctions");
            seed(2); invoke(p, "render", Object[].class, snapshot());
            check(rows[26].text.equals("Hunger: Satisfied"), "restore from blank/missing");
        } else if (scenario.equals("unicode")) {
            seed(6); invoke(p, "render", Object[].class, snapshot());
            check(rows[26].text.equals("Hunger: Faim \u00e9 \ud83d\ude80"), "ordinary UTF-8 including supplementary");
            check(rows[27].text.length() == 1008 && rows[28].text.equals("Rest: A\0B"), "long/NUL transport");
        } else if (scenario.equals("copy")) {
            ((long[]) raw[0])[50] = 0; ((byte[][]) raw[1])[27][0] = 'X';
            check(decoded.label(26).equals("Hunger: Satisfied"), "decoded copy independent");
            check(ActivityHudSnapshot.decode(snapshot()).label(26).equals("Hunger: Satisfied"), "native copy independent");
        } else if (scenario.equals("malformed")) {
            check(ActivityHudSnapshot.decode(new Object[]{new long[50], new byte[27][]}) == null, "reject older shape");
            ((long[]) raw[0])[52] = 2;
            check(ActivityHudSnapshot.decode(raw) == null, "reject invalid availability");
            raw = snapshot(); ((byte[][]) raw[1])[29] = null;
            check(ActivityHudSnapshot.decode(raw) == null, "reject null text");
        }
        // Every scenario must survive inactive, unready, invalid and reloaded states.
        seed(0); invoke(p, "render", Object[].class, snapshot());
        check(((TextView) field(p, "value")).text.equals("No active game"), "inactive message");
        for (TextView row : rows) if (row != null) check(row.text.isEmpty(), "all visible data cleared");
        check(((View) field(p, "activityStatus")).visibility == View.GONE, "menu hides rows");
        seed(1); invoke(p, "render", Object[].class, snapshot());
        check(((TextView) field(p, "value")).text.equals("Waiting for the first game redraw"), "unready message");
        invoke(p, "render", Object[].class, null);
        check(((TextView) field(p, "value")).text.equals("Snapshot unavailable"), "invalid message");
        seed(3); invoke(p, "render", Object[].class, snapshot());
        check(rows[28].text.equals("Rest: Dead Tired"), "reload new state");
        common(p, rows, font);
        check(((TextView) field(p, "status")).text.contains(font.description), "footer retained");
        check(fontCalls == context.assets.modernCalls + context.assets.legacyCalls, "no repeated font load");
        System.out.println("needs JNI/UI host scenario passed: " + scenario);
    }
}
