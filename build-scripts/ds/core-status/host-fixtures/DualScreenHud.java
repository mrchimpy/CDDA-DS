package com.cleverraven.cataclysmdda;

// Host-only shim for the actual exported JNI function. Not packaged in the APK.
final class DualScreenHud {
    static native Object[] nativeSnapshot();
}
