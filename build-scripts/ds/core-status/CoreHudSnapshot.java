package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;

/** Immutable decoded copy. No Android classes, live game objects, or game actions. */
final class CoreHudSnapshot {
    static final int CORE_COUNT = 6;
    private static final int FIELD_COUNT = 24;
    private static final String[] LABELS = {
        "Strength", "Dexterity", "Intelligence", "Perception", "Speed", "Focus"
    };
    final boolean active;
    final boolean ready;
    final long current;
    final long maximum;
    final long sequence;
    final long ageMs;
    final String movementMode;
    private final long[] values;

    private CoreHudSnapshot(long[] data, byte[] movement) {
        values = data.clone();
        active = values[0] != 0;
        ready = active && values[1] != 0 && values[2] >= 0 && values[3] > 0;
        current = ready ? values[2] : 0;
        maximum = ready ? values[3] : 0;
        sequence = values[4];
        ageMs = Math.max(0, values[5]);
        String label = ready ? new String(movement, StandardCharsets.UTF_8) : "";
        movementMode = ready && label.isEmpty() ? "Unknown" : label;
        // Invalid/menu snapshots must never retain another character's readouts.
        if (!ready) {
            for (int i = 6; i < FIELD_COUNT; i++) values[i] = 0;
        }
    }

    static CoreHudSnapshot decode(Object[] raw) {
        if (raw == null || raw.length != 2 || !(raw[0] instanceof long[])
                || !(raw[1] instanceof byte[])) return null;
        long[] data = (long[]) raw[0];
        if (data.length != FIELD_COUNT || data[0] < 0 || data[0] > 1
                || data[1] < 0 || data[1] > 1) return null;
        return new CoreHudSnapshot(data, (byte[]) raw[1]);
    }

    long healthCurrent(int part) {
        if (part < 0 || part >= 6) throw new IndexOutOfBoundsException();
        return values[6 + part * 2];
    }

    long healthMaximum(int part) {
        if (part < 0 || part >= 6) throw new IndexOutOfBoundsException();
        return values[7 + part * 2];
    }

    long coreValue(int field) {
        if (field < 0 || field >= CORE_COUNT) throw new IndexOutOfBoundsException();
        return values[18 + field];
    }

    String coreLabel(int field) {
        return LABELS[field] + ": " + coreValue(field);
    }
}
