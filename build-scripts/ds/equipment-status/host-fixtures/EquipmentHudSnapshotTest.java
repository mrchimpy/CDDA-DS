package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

final class EquipmentHudSnapshotTest {
    private static native void seed(int scenario);
    private static void check(boolean value) {
        if (!value) throw new AssertionError("Equipment snapshot check failed");
    }
    private static Object[] raw() { return DualScreenHud.nativeSnapshot(); }
    private static ActivityHudSnapshot snapshot() { return ActivityHudSnapshot.decode(raw()); }

    public static void main(String[] args) {
        System.load(args[0]);
        seed(1);
        Object[] wire = raw();
        check(((long[]) wire[0]).length == 41 && ((byte[][]) wire[1]).length == 18);
        ActivityHudSnapshot first = ActivityHudSnapshot.decode(wire);
        check(first != null && first.core.ready && first.core.current == 25 && first.core.maximum == 100);
        long[] expected = {5, 0, -1, 4, 75, 137};
        for (int i = 0; i < 6; i++) {
            check(first.core.coreValue(i) == expected[i]);
            check(first.core.healthCurrent(i) == 20 + i && first.core.healthMaximum(i) == 80 + i);
        }
        String[] labels = {"Weariness", "Activity", "Transition", "Weary Malus", "Pain", "Date", "Time",
            "Place", "Weather", "Lighting", "Wind", "Temperature", "Wield", "Style", "Bionic Power", "Sound", "Mood"};
        String[] values = {"Fresh", "None", "|||||", "+ 0%", "", "Thursday, May 20", "Morning", "road",
            "Clear", "bright", "Light Breeze", "-", "fists", "No style", "--", "0", ":|"};
        for (int i = 0; i < 17; i++) {
            check(first.available(i) && first.text(i).equals(values[i]));
            check(first.label(i).equals(labels[i] + ": " + (values[i].isEmpty() ? "\u2014" : values[i])));
        }
        ((long[]) wire[0])[18] = 99;
        ((byte[][]) wire[1])[13][0] = 'X';
        check(first.core.coreValue(0) == 5 && first.text(12).equals("fists"));
        seed(2);
        ActivityHudSnapshot changed = snapshot();
        char[] padding = new char[512]; Arrays.fill(padding, 'x');
        check(changed.text(12).equals(new String(padding) + " / epee \u2694 \ud83e\udded\0tail"));
        check(changed.text(13).equals("Karate") && changed.text(14).equals("2.50 kJ"));
        check(changed.text(15).equals("99") && changed.text(16).equals(":)"));
        check(first.text(12).equals("fists"));
        seed(4);
        ActivityHudSnapshot special = snapshot();
        check(special.label(12).equals("Wield: \u2014"));
        check(!special.available(13) && special.label(13).equals("Style: Unavailable"));
        check(special.label(14).equals("Bionic Power: 0 J") && special.label(15).equals("Sound: 0"));
        wire = raw();
        ((byte[][]) wire[1])[17] = " \t\n".getBytes(StandardCharsets.UTF_8);
        check(ActivityHudSnapshot.decode(wire).label(16).equals("Mood: \u2014"));
        for (int scenario : new int[] {0, 3, 5}) {
            seed(scenario);
            ActivityHudSnapshot empty = snapshot();
            check(!empty.core.ready && empty.core.movementMode.isEmpty());
            for (int i = 0; i < 17; i++) check(!empty.available(i) && empty.text(i).isEmpty() && empty.label(i).isEmpty());
        }
        seed(1);
        check(snapshot().text(12).equals("fists"));
        check(ActivityHudSnapshot.decode(null) == null);
        check(ActivityHudSnapshot.decode(new Object[0]) == null);
        check(ActivityHudSnapshot.decode(new Object[] {new long[41], new byte[17][]}) == null);
        check(ActivityHudSnapshot.decode(new Object[] {new long[40], new byte[18][]}) == null);
        check(ActivityHudSnapshot.decode(new Object[] {"wrong", "types"}) == null);
        for (int i = 0; i < 18; i++) {
            wire = raw(); ((byte[][]) wire[1])[i] = null;
            check(ActivityHudSnapshot.decode(wire) == null);
        }
        for (int i = 24; i < 41; i++) {
            for (long bad : new long[] {-1, 2}) {
                wire = raw(); ((long[]) wire[0])[i] = bad;
                check(ActivityHudSnapshot.decode(wire) == null);
            }
        }
        for (int i : new int[] {-1, 17}) {
            try { first.label(i); throw new AssertionError("Expected bounds check"); }
            catch (IndexOutOfBoundsException expectedError) { }
        }
        System.out.println("equipment real JNI round-trip passed");
    }
}
