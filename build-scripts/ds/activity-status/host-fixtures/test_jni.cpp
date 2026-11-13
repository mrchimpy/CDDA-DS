#include "ds_hud.h"
#include <jni.h>

extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_ActivityHudSnapshotTest_nativeSet( JNIEnv *, jclass, jint mode )
{
    if( mode == 0 ) { ds_hud::end_session(); return; }
    if( mode == 1 ) { ds_hud::begin_session(); return; }
    ds_hud::body_health health;
    health.current.fill( 30 );
    health.maximum.fill( 80 );
    ds_hud::core_status core;
    core.strength = -2;
    core.dexterity = 0;
    core.intelligence = 11;
    core.perception = 4;
    core.speed = 75;
    core.focus = 140;
    core.movement_mode = "crouch (C)";
    ds_hud::activity_status status;
    status.available.fill( true );
    status.text = { "Fresh", "Moderate", "||||\\", "+ 25%", "" };
    if( mode == 3 ) {
        core.movement_mode = "run (R)";
        status.text = { "Weary", "Extreme", "..\\||", "+100%", "Intense pain" };
    } else if( mode == 4 ) {
        status.available[1] = false;
        status.text[1] = "This must not appear";
    } else if( mode == 5 ) {
        status.text[0] = u8"caf\u00e9 \U0001f4aa";
        status.text[1] = std::string( "A\0B", 3 );
        status.text[2] = std::string( 20000, '|' );
    }
    ds_hud::publish( 25, mode == 6 ? 0 : 100, health, core, status );
}
