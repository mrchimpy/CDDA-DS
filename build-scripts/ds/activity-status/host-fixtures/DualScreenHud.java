package com.cleverraven.cataclysmdda;

/** Host-only JNI entry point; this does NOT exercise Android Presentation. */
final class DualScreenHud {
    static native Object[] nativeSnapshot();
}
