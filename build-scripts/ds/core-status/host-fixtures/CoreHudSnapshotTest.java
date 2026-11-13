package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;

public final class CoreHudSnapshotTest {
    private static native void begin();
    private static native void end();
    private static native void publish(int mode);
    private static void check(boolean value) {
        if (!value) throw new AssertionError();
    }
    private static CoreHudSnapshot state() {
        CoreHudSnapshot result = CoreHudSnapshot.decode(DualScreenHud.nativeSnapshot());
        check(result != null);
        return result;
    }
    public static void main(String[] args) {
        System.load(args[0]);
        end();
        check(!state().active && !state().ready && state().movementMode.isEmpty());
        begin();
        check(state().active && !state().ready);
        publish(0);
        CoreHudSnapshot normal = state();
        check(normal.active && normal.ready && normal.current == 2128 && normal.maximum == 8500);
        long[] expected = {7, 6, 11, 9, 82, 137};
        String[] labels = {"Strength: 7", "Dexterity: 6", "Intelligence: 11",
                           "Perception: 9", "Speed: 82", "Focus: 137"};
        for (int i = 0; i < 6; i++) {
            check(normal.coreValue(i) == expected[i]);
            check(normal.coreLabel(i).equals(labels[i]));
            check(normal.healthCurrent(i) == 10 + i && normal.healthMaximum(i) == 100 + i);
        }
        check(normal.movementMode.equals("walk (W)") && normal.ageMs >= 0);
        publish(1);
        check(state().movementMode.equals("\u6f5c\u884c \ud83d\udeb6 (C)"));
        publish(2);
        check(state().movementMode.equals("run (R)") && state().coreValue(4) == 64);
        check(state().coreValue(1) == 3 && normal.coreValue(1) == 6);
        publish(3);
        check(state().movementMode.equals("Unknown"));
        publish(4);
        check(state().movementMode.length() == 8192);
        publish(5);
        check(state().coreValue(0) == 0 && state().coreValue(3) == -2 && state().coreValue(5) == 200);
        publish(6);
        check(!state().ready && state().coreValue(0) == 0 && state().movementMode.isEmpty());
        publish(0);
        Object[] raw = DualScreenHud.nativeSnapshot();
        CoreHudSnapshot immutable = CoreHudSnapshot.decode(raw);
        ((long[]) raw[0])[18] = -999;
        ((byte[]) raw[1])[0] = 0;
        check(immutable.coreValue(0) == 7 && immutable.movementMode.equals("walk (W)"));
        check(CoreHudSnapshot.decode(null) == null);
        check(CoreHudSnapshot.decode(new Object[] {new long[18], new byte[0]}) == null);
        check(CoreHudSnapshot.decode(new Object[] {new long[24], "walk"}) == null);
        check(CoreHudSnapshot.decode(new Object[] {new byte[24], new byte[0]}) == null);
        check(CoreHudSnapshot.decode(new Object[0]) == null);
        long[] badFlags = new long[24];
        badFlags[0] = 2;
        check(CoreHudSnapshot.decode(new Object[] {badFlags, new byte[0]}) == null);
        long[] menu = new long[24];
        menu[1] = 1; menu[2] = 10; menu[3] = 100; menu[18] = 99;
        CoreHudSnapshot noGame = CoreHudSnapshot.decode(
            new Object[] {menu, "run (R)".getBytes(StandardCharsets.UTF_8)});
        check(!noGame.ready && noGame.coreValue(0) == 0 && noGame.movementMode.isEmpty());
        long oldSequence = state().sequence;
        end();
        check(!state().active && !state().ready && state().coreValue(5) == 0);
        check(state().movementMode.isEmpty() && state().sequence > oldSequence);
        begin();
        check(!state().ready && state().healthCurrent(0) == 0 && state().coreValue(0) == 0);
        publish(2);
        check(state().coreValue(1) == 3);
        end();
        System.out.println("Core HUD Java decoder and real JNI round-trip passed");
    }
}
