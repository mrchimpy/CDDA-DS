package com.cleverraven.cataclysmdda;

/** Host-only JNI entrypoint stand-in; does not test Android Presentation. */
final class DualScreenHud {
    static native Object[] nativeSnapshot();
}
