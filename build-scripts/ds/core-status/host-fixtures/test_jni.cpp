#include "ds_hud.h"
#include <jni.h>

extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_CoreHudSnapshotTest_begin( JNIEnv *, jclass )
{
    ds_hud::begin_session();
}

extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_CoreHudSnapshotTest_end( JNIEnv *, jclass )
{
    ds_hud::end_session();
}

extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_CoreHudSnapshotTest_publish( JNIEnv *, jclass, jint mode )
{
    ds_hud::body_health health;
    for( int i = 0; i < 6; ++i ) {
        health.current[i] = 10 + i;
        health.maximum[i] = 100 + i;
    }
    ds_hud::core_status core{ 7, 6, 11, 9, 82, 137, "walk (W)" };
    switch( mode ) {
        case 1: core.movement_mode = u8"\u6f5c\u884c \U0001f6b6 (C)"; break;
        case 2: core.movement_mode = "run (R)"; core.speed = 64; core.dexterity = 3; break;
        case 3: core.movement_mode.clear(); break;
        case 4: core.movement_mode = std::string( 8192, 'm' ); break;
        case 5: core.strength = 0; core.perception = -2; core.focus = 200; break;
        default: break;
    }
    ds_hud::publish( mode == 6 ? -1 : 2128, 8500, health, core );
}
