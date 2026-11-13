package com.cleverraven.cataclysmdda;

import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Display;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.ScrollView;
import android.widget.TextView;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Executes production UI calls against substitutes, never a real Android renderer. */
public final class PresentationHostTest {
    static void check(boolean value, String why) {
        if (!value) throw new AssertionError(why);
    }
    static List<TextView> texts(View root) {
        List<TextView> result = new ArrayList<>();
        if (root instanceof TextView) result.add((TextView) root);
        if (root instanceof ViewGroup) {
            for (View v : ((ViewGroup) root).children) result.addAll(texts(v));
        }
        return result;
    }
    static Object field(Object o, String name) throws Exception {
        Field f = o.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(o);
    }
    static void invoke(Object o, String name, Class<?> type, Object value) throws Exception {
        Method m = o.getClass().getDeclaredMethod(name, type); m.setAccessible(true); m.invoke(o, value);
    }
    static void common(Presentation p, HudTypeface font) {
        check(p.window.background.color == Color.BLACK, "window background");
        check(p.content.background == Color.BLACK, "scroll background");
        check(((ViewGroup) p.content).children.get(0).background == Color.BLACK, "content background");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE) != 0, "focus flag retained");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_DIM_BEHIND) == 0, "no dim");
        check(!p.content.focusable, "scroll not focusable");
        check(((ScrollView) p.content).fill, "fill viewport retained");
        check(((ViewGroup) p.content).descendants == ViewGroup.FOCUS_BLOCK_DESCENDANTS, "descendant block retained");
        List<TextView> all = texts(p.content);
        check(all.size() == 42, "all title/value/labels/footer present: " + all.size());
        for (TextView t : all) {
            check(t.face == font.typeface, "one shared face: " + t.text);
            check(!t.focusable, "no text keyboard focus");
            check(t.color == Color.WHITE, "text color unchanged");
            check(t.spacing == 0f, "no additional letter spacing");
            check(t.features.equals("'liga' 0, 'clig' 0, 'kern' 0"), "consistent shaping flags");
        }
    }
    public static void main(String[] args) throws Exception {
        String mode = args[0]; Context context = new Context();
        Build.VERSION.SDK_INT = mode.equals("legacy") || mode.equals("legacy-failure") ? 24 : 35;
        context.assets.failPrimary = mode.equals("primary-failure") || mode.equals("legacy-failure");
        context.assets.failFallback = mode.equals("missing-fallback");
        context.assets.failModern = mode.equals("modern-failure");
        context.assets.failBuilder = mode.equals("builder-failure");
        Class<?> c = Class.forName("com.cleverraven.cataclysmdda.DualScreenHud$HudPresentation");
        Constructor<?> ctor = c.getDeclaredConstructor(Context.class, Display.class); ctor.setAccessible(true);
        Presentation p = (Presentation) ctor.newInstance(context, new Display());
        invoke(p, "onCreate", Bundle.class, new Bundle());
        HudTypeface f = (HudTypeface) field(p, "hudFont");
        if (context.assets.failPrimary) {
            check(f.typeface == Typeface.MONOSPACE, "explicit emergency fallback");
            check(f.description.contains("Android monospace"), "fallback identification");
        } else {
            check(f.typeface.primary.equals(HudTypeface.PRIMARY), "bundled Terminus primary");
            if (mode.equals("normal")) {
                check(f.typeface.fallback.equals(HudTypeface.FALLBACK), "bundled Unifont fallback");
                check(f.typeface.system.equals("monospace"), "final system family");
                check(f.description.equals("Terminus + Unifont"), "normal diagnostic");
            } else {
                check(f.description.contains("system glyph fallback"), "degraded-chain diagnostic");
            }
        }
        if (Build.VERSION.SDK_INT < 29) check(context.assets.modernCalls == 0, "API gate");
        common(p, f);
        check(((TextView) field(p,"status")).text.contains(f.description), "waiting font footer");
        int calls = context.assets.modernCalls + context.assets.legacyCalls;
        long[] values = new long[50]; values[0]=1; values[1]=1; values[2]=50; values[3]=100;
        values[4]=99; values[5]=250;
        for (int i=0; i<6; i++) { values[6+i*2]=40; values[7+i*2]=80; }
        for (int i=18; i<24; i++) values[i]=i;
        byte[][] labels = new byte[27][];
        labels[0]="walk (W)".getBytes(StandardCharsets.UTF_8);
        for (int i=0; i<26; i++) {
            values[24+i]=1; labels[i+1]=("field " + i).getBytes(StandardCharsets.UTF_8);
        }
        labels[3]="|||||".getBytes(StandardCharsets.UTF_8);
        labels[20]="..\\||".getBytes(StandardCharsets.UTF_8);
        invoke(p,"render",Object[].class,new Object[]{values,labels});
        common(p,f);
        TextView[] rows=(TextView[])field(p,"activityValues");
        check(rows.length==26, "26 widget slots retained");
        check(rows[2].text.equals("Transition: |||||"), "transition unchanged");
        check(rows[19].text.equals("Oxygen: ..\\||"), "oxygen unchanged");
        check(rows[25].text.equals("Worn feet: field 25"), "last row retained");
        check(((TextView)field(p,"value")).size==22f, "stamina text size retained");
        check(((TextView)field(p,"status")).text.contains(f.description), "active font footer");
        values[0]=0;
        invoke(p,"render",Object[].class,new Object[]{values,labels});
        common(p,f);
        check(((TextView)field(p,"value")).text.equals("No active game"), "menu text retained");
        for (TextView row: rows) check(row.text.isEmpty(), "session clearing retained");
        invoke(p,"render",Object[].class,null);
        common(p,f);
        check(((TextView)field(p,"value")).text.equals("Snapshot unavailable"), "error state retained");
        check(((TextView)field(p,"status")).text.contains(f.description), "error font footer");
        check(calls==context.assets.modernCalls+context.assets.legacyCalls, "no font reload during polling/render");
        System.out.println("presentation host substitute passed: " + mode);
    }
}
