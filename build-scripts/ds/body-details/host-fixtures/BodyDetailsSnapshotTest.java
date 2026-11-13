package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;

final class BodyDetailsSnapshotTest {
    private static native void seed(int version);
    private static void check(boolean value) {
        if (!value) throw new AssertionError();
    }
    private static ActivityHudSnapshot state() {
        ActivityHudSnapshot result = ActivityHudSnapshot.decode(DualScreenHud.nativeSnapshot());
        check(result != null);
        return result;
    }
    private static void cleared(ActivityHudSnapshot s) {
        check(!s.core.ready);
        for (int i = 0; i < ActivityHudSnapshot.STATUS_COUNT; i++) {
            check(!s.available(i) && s.text(i).isEmpty() && s.label(i).isEmpty());
        }
        check(s.core.coreValue(0) == 0 && s.core.movementMode.isEmpty());
    }
    public static void main(String[] args) {
        System.load(args[0]);
        seed(0);
        Object[] raw = DualScreenHud.nativeSnapshot();
        check(((long[]) raw[0]).length == 50 && ((byte[][]) raw[1]).length == 27);
        ActivityHudSnapshot s = ActivityHudSnapshot.decode(raw);
        check(s.core.current == 25 && s.core.maximum == 100);
        check(s.core.coreValue(0) == -2 && s.core.coreValue(1) == 0);
        check(s.core.coreValue(5) == 137 && s.core.movementMode.equals("walk (W)"));
        for (int i = 0; i < 6; i++) {
            check(s.core.healthCurrent(i) == 10 + i && s.core.healthMaximum(i) == 100 + i);
        }
        for (int i = 0; i < 17; i++) check(s.text(i).equals("slot " + i));
        check(s.label(17).equals("Body comfort: Comfortable"));
        check(s.label(18).equals("Comfort trend: (Rising!)"));
        check(s.label(19).equals("Oxygen: |||.."));
        check(s.label(20).equals("Worn head: helmet"));
        check(s.text(21).length() > 500 && s.text(21).endsWith(" \u2191 \uD83D\uDE00"));
        check(s.text(22).equals("a\u0000b"));
        check(s.label(25).equals("Worn feet: boots"));
        ((long[]) raw[0])[18] = 999;
        ((byte[][]) raw[1])[21][0] = 0;
        check(s.core.coreValue(0) == -2 && s.text(20).equals("helmet"));
        seed(1);
        ActivityHudSnapshot updated = state();
        check(s.text(20).equals("helmet") && updated.text(17).equals("Chilly"));
        check(updated.available(19) && updated.label(19).equals("Oxygen: \u2014"));
        check(updated.label(18).equals("Comfort trend: \u2014"));
        check(!updated.available(20) && updated.label(20).equals("Worn head: Unavailable"));
        check(updated.label(23).equals("Worn hands: \u2014"));
        check(updated.text(21).equals("jacket > 2 items") && updated.text(25).equals("sandals"));
        Object[] zero = DualScreenHud.nativeSnapshot();
        ((byte[][]) zero[1])[26] = "0".getBytes(StandardCharsets.UTF_8);
        check(ActivityHudSnapshot.decode(zero).label(25).equals("Worn feet: 0"));
        check(ActivityHudSnapshot.decode(null) == null);
        check(ActivityHudSnapshot.decode(new Object[0]) == null);
        check(ActivityHudSnapshot.decode(new Object[] {new long[49], new byte[27][]}) == null);
        check(ActivityHudSnapshot.decode(new Object[] {new long[50], new byte[26][]}) == null);
        Object[] bad = DualScreenHud.nativeSnapshot();
        ((long[]) bad[0])[49] = 2;
        check(ActivityHudSnapshot.decode(bad) == null);
        bad = DualScreenHud.nativeSnapshot();
        ((byte[][]) bad[1])[26] = null;
        check(ActivityHudSnapshot.decode(bad) == null);
        try { s.label(26); throw new AssertionError(); }
        catch (IndexOutOfBoundsException expected) { /* correct */ }
        seed(2); cleared(state());
        seed(3); check(!state().core.active); cleared(state());
        seed(4); check(state().core.active); cleared(state());
        seed(0); check(state().text(20).equals("helmet"));
        seed(3);
        System.out.println("body details real JNI round-trip passed");
    }
}
