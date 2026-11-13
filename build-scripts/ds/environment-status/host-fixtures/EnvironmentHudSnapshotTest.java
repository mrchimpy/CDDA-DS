package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;

public final class EnvironmentHudSnapshotTest {
    private static native void seed(int which);
    private static void check(boolean condition) {
        if (!condition) throw new AssertionError();
    }
    private static ActivityHudSnapshot read() {
        ActivityHudSnapshot s = ActivityHudSnapshot.decode(DualScreenHud.nativeSnapshot());
        check(s != null);
        return s;
    }
    public static void main(String[] args) {
        System.load(args[0]);
        check(ActivityHudSnapshot.STATUS_COUNT == 12);
        seed(0);
        ActivityHudSnapshot s = read();
        check(!s.core.active && !s.core.ready);
        seed(1);
        s = read();
        check(s.core.active && !s.core.ready);
        for (int i = 0; i < 12; i++) check(s.label(i).isEmpty() && s.text(i).isEmpty());
        seed(2);
        s = read();
        String[] expected = {"Weariness: Fresh", "Activity: None", "Transition: |||||",
            "Weary Malus: + 0%", "Pain: \u2014", "Date: Thursday, May 20", "Time: ???",
            "Place: road", "Weather: Clear", "Lighting: bright", "Wind: Light Breeze \u2197",
            "Temperature: -"};
        for (int i = 0; i < 12; i++) check(s.available(i) && s.label(i).equals(expected[i]));
        check(s.core.current == 23 && s.core.maximum == 100);
        check(s.core.healthCurrent(0) == 30 && s.core.healthMaximum(5) == 80);
        check(s.core.coreLabel(0).equals("Strength: 5"));
        check(s.core.coreLabel(1).equals("Dexterity: 0"));
        check(s.core.coreLabel(2).equals("Intelligence: -2"));
        check(s.core.coreLabel(5).equals("Focus: 137"));
        Object[] raw = DualScreenHud.nativeSnapshot();
        ActivityHudSnapshot copy = ActivityHudSnapshot.decode(raw);
        ((long[])raw[0])[24 + 6] = 0;
        ((byte[][])raw[1])[7][0] = 0;
        check(copy.available(6) && copy.text(6).equals("???"));
        seed(3);
        s = read();
        check(s.text(6).equals("08:12:34"));
        check(s.text(7).endsWith("\ud83c\udf0d\u0000") && s.text(7).length() == 2003);
        check(s.label(8).equals("Weather: Rain") && s.label(9).equals("Lighting: dark"));
        check(s.label(11).equals("Temperature: -5\u00b0C"));
        seed(4);
        s = read();
        check(!s.available(8) && s.text(8).isEmpty() && s.label(8).equals("Weather: Unavailable"));
        raw = DualScreenHud.nativeSnapshot();
        ((byte[][])raw[1])[6] = "  \n\t".getBytes(StandardCharsets.UTF_8);
        check(ActivityHudSnapshot.decode(raw).label(5).equals("Date: \u2014"));
        check(ActivityHudSnapshot.decode(null) == null);
        check(ActivityHudSnapshot.decode(new Object[0]) == null);
        check(ActivityHudSnapshot.decode(new Object[]{new long[29], new byte[6][]}) == null);
        raw = DualScreenHud.nativeSnapshot();
        ((long[])raw[0])[35] = 2;
        check(ActivityHudSnapshot.decode(raw) == null);
        raw = DualScreenHud.nativeSnapshot();
        ((byte[][])raw[1])[12] = null;
        check(ActivityHudSnapshot.decode(raw) == null);
        seed(0);
        s = read();
        for (int i = 0; i < 12; i++) check(s.label(i).isEmpty() && !s.available(i));
        seed(1);
        s = read();
        for (int i = 0; i < 12; i++) check(s.text(i).isEmpty());
        seed(2);
        check(read().label(6).equals("Time: ???"));
        System.out.println("environment real JNI round-trip passed");
    }
}
