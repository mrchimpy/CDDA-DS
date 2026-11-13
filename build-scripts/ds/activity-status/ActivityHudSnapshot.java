package com.cleverraven.cataclysmdda;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Immutable decoded copy of the five game-rendered status widgets. */
final class ActivityHudSnapshot {
    static final int STATUS_COUNT = 5;
    static final int TRANSITION = 2;
    private static final int CORE_FIELDS = 24;
    private static final int FIELD_COUNT = CORE_FIELDS + STATUS_COUNT;
    private static final String[] LABELS = {
        "Weariness", "Activity", "Transition", "Weary Malus", "Pain"
    };
    final CoreHudSnapshot core;
    private final String[] texts = new String[STATUS_COUNT];
    private final boolean[] available = new boolean[STATUS_COUNT];

    private ActivityHudSnapshot(CoreHudSnapshot core, long[] values, byte[][] encoded) {
        this.core = core;
        for (int i = 0; i < STATUS_COUNT; i++) {
            available[i] = core.ready && values[CORE_FIELDS + i] == 1;
            texts[i] = available[i] ? new String(encoded[i + 1], StandardCharsets.UTF_8) : "";
        }
    }

    static ActivityHudSnapshot decode(Object[] raw) {
        if (raw == null || raw.length != 2 || !(raw[0] instanceof long[])
                || !(raw[1] instanceof byte[][])) return null;
        long[] values = ((long[]) raw[0]).clone();
        byte[][] texts = (byte[][]) raw[1];
        if (values.length != FIELD_COUNT || texts.length != STATUS_COUNT + 1) return null;
        for (byte[] text : texts) if (text == null) return null;
        for (int i = CORE_FIELDS; i < FIELD_COUNT; i++) {
            if (values[i] < 0 || values[i] > 1) return null;
        }
        CoreHudSnapshot core = CoreHudSnapshot.decode(new Object[] {
            Arrays.copyOf(values, CORE_FIELDS), texts[0]
        });
        return core == null ? null : new ActivityHudSnapshot(core, values, texts);
    }

    boolean available(int field) {
        check(field);
        return available[field];
    }

    String text(int field) {
        check(field);
        return texts[field];
    }

    String label(int field) {
        check(field);
        if (!core.ready) return "";
        // A dash means CDDA supplied blank text, NOT an invented numeric zero.
        String value = !available[field] ? "Unavailable"
            : texts[field].trim().isEmpty() ? "\u2014" : texts[field];
        return LABELS[field] + ": " + value;
    }

    private static void check(int field) {
        if (field < 0 || field >= STATUS_COUNT) throw new IndexOutOfBoundsException();
    }
}
