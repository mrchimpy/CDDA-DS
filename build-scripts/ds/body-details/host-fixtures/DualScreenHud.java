package com.cleverraven.cataclysmdda;

// Host-only declaration: calls the production JNI bridge without Android UI classes.
final class DualScreenHud {
    static native Object[] nativeSnapshot();
}
