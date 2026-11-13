package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;

public final class ActivityHudSnapshotTest {
    private static native void nativeSet(int mode);
    private static void check(boolean condition) {
        if (!condition) throw new AssertionError("Activity snapshot check failed");
    }
    private static ActivityHudSnapshot read() {
        ActivityHudSnapshot s = ActivityHudSnapshot.decode(DualScreenHud.nativeSnapshot());
        check(s != null);
        return s;
    }
    private static Object[] fixture() {
        long[] n = new long[29];
        n[0] = 1; n[1] = 1; n[2] = 30; n[3] = 100; n[23] = 150;
        byte[][] t = new byte[6][];
        for (int i = 0; i < t.length; i++) t[i] = ("t" + i).getBytes(StandardCharsets.UTF_8);
        for (int i = 24; i < 29; i++) n[i] = 1;
        return new Object[] {n, t};
    }
    private static void cleared(ActivityHudSnapshot s) {
        check(!s.core.ready && s.core.current == 0 && s.core.coreValue(5) == 0);
        check(s.core.movementMode.isEmpty());
        for (int i = 0; i < 5; i++) {
            check(!s.available(i) && s.text(i).isEmpty() && s.label(i).isEmpty());
        }
    }
    public static void main(String[] args) {
        System.load(args[0]);
        nativeSet(0); check(!read().core.active); cleared(read());
        nativeSet(2); cleared(read()); // Publishing outside a session is ignored.
        nativeSet(1); check(read().core.active); cleared(read());
        nativeSet(2);
        ActivityHudSnapshot s = read();
        check(s.core.ready && s.core.current == 25 && s.core.maximum == 100);
        check(s.core.healthCurrent(5) == 30 && s.core.healthMaximum(0) == 80);
        check(s.core.coreValue(0) == -2 && s.core.coreValue(1) == 0 && s.core.coreValue(5) == 140);
        check(s.core.movementMode.equals("crouch (C)"));
        check(s.label(0).equals("Weariness: Fresh"));
        check(s.label(1).equals("Activity: Moderate"));
        check(s.text(2).equals("||||\\"));
        check(s.label(3).equals("Weary Malus: + 25%"));
        check(s.available(4) && s.text(4).isEmpty() && s.label(4).equals("Pain: \u2014"));
        nativeSet(3);
        check(read().text(0).equals("Weary") && read().text(4).equals("Intense pain"));
        check(read().core.movementMode.equals("run (R)"));
        check(s.text(0).equals("Fresh")); // Earlier reader remains immutable.
        nativeSet(4);
        check(!read().available(1) && read().label(1).equals("Activity: Unavailable"));
        check(read().text(1).isEmpty() && read().available(4));
        nativeSet(5);
        check(read().text(0).equals("caf\u00e9 \ud83d\udcaa"));
        check(read().text(1).equals("A\u0000B"));
        check(read().text(2).length() == 20000);
        nativeSet(6); cleared(read());
        nativeSet(2); nativeSet(0); cleared(read());
        nativeSet(1); cleared(read());
        check(ActivityHudSnapshot.decode(null) == null);
        check(ActivityHudSnapshot.decode(new Object[0]) == null);
        check(ActivityHudSnapshot.decode(new Object[] {"wrong", new byte[6][]}) == null);
        Object[] raw = fixture();
        s = ActivityHudSnapshot.decode(raw); check(s != null);
        ((long[]) raw[0])[23] = 1;
        ((byte[][]) raw[1])[1][0] = 'x';
        check(s.core.coreValue(5) == 150 && s.text(0).equals("t1"));
        raw = fixture(); raw[0] = new long[28]; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); raw[1] = new Object[6]; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); raw[1] = new byte[5][]; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); ((byte[][]) raw[1])[2] = null; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); ((long[]) raw[0])[24] = 2; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); ((long[]) raw[0])[24] = -1; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); ((long[]) raw[0])[0] = 2; check(ActivityHudSnapshot.decode(raw) == null);
        raw = fixture(); ((long[]) raw[0])[0] = 0; cleared(ActivityHudSnapshot.decode(raw));
        raw = fixture(); ((long[]) raw[0])[1] = 0; cleared(ActivityHudSnapshot.decode(raw));
        raw = fixture(); ((long[]) raw[0])[2] = -1; cleared(ActivityHudSnapshot.decode(raw));
        raw = fixture(); ((long[]) raw[0])[3] = 0; cleared(ActivityHudSnapshot.decode(raw));
        raw = fixture(); ((byte[][]) raw[1])[5] = "  ".getBytes(StandardCharsets.UTF_8);
        check(ActivityHudSnapshot.decode(raw).label(4).equals("Pain: \u2014"));
        boolean threw = false;
        try { s.text(5); } catch (IndexOutOfBoundsException expected) { threw = true; }
        check(threw);
        threw = false;
        try { s.available(-1); } catch (IndexOutOfBoundsException expected) { threw = true; }
        check(threw);
        System.out.println("activity real JNI round-trip passed");
    }
}
