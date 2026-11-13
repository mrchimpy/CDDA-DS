#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <stdexcept>
#include <thread>

static void sample( int n )
{
    ds_hud::body_health hp;
    hp.current.fill( n );
    hp.maximum.fill( n + 100 );
    ds_hud::core_status core;
    core.strength = n;
    core.dexterity = -n;
    core.focus = 137;
    core.movement_mode = "walk (W)";
    ds_hud::activity_status fields;
    for( std::size_t i = 0; i < fields.text.size(); ++i ) {
        fields.text[i] = std::to_string( n ) + ":" + std::to_string( i );
        fields.available[i] = true;
    }
    ds_hud::publish( n, n + 200, hp, core, fields );
    fields.text.fill( "caller changed" ); // Must not affect published data.
}

int main()
{
    static_assert( ds_hud::activity_field_count == 12 );
    static_assert( ds_hud::wire_field_count == 36 );
    ds_hud::end_session();
    sample( 7 );
    assert( !ds_hud::read().active && !ds_hud::read().ready );
    {
        ds_hud::session_scope session;
        sample( 7 );
        auto s = ds_hud::read();
        assert( s.ready && s.core.focus == 137 && s.activity.text[11] == "7:11" );
        s.activity.text[11] = "reader changed";
        assert( ds_hud::read().activity.text[11] == "7:11" );
        const auto wire = ds_hud::wire_values( s );
        assert( wire[18] == 7 && wire[19] == -7 && wire[23] == 137 );
        for( int i = 24; i < 36; ++i ) { assert( wire[i] == 1 ); }
        std::atomic<bool> done{false};
        std::thread writer( [&done]() {
            for( int n = 1; n <= 3000; ++n ) { sample( n ); }
            done = true;
        } );
        do {
            const auto copy = ds_hud::read();
            assert( copy.current == copy.core.strength );
            for( int i = 0; i < 12; ++i ) {
                assert( copy.activity.text[i] == std::to_string( copy.current ) + ":" + std::to_string( i ) );
            }
        } while( !done );
        writer.join();
        ds_hud::publish( -1, 0 );
        s = ds_hud::read();
        assert( s.active && !s.ready && s.core.movement_mode.empty() );
        for( int i = 0; i < 12; ++i ) {
            assert( s.activity.text[i].empty() && !s.activity.available[i] );
        }
    }
    assert( !ds_hud::read().active );
    try {
        ds_hud::session_scope session;
        sample( 10 );
        throw std::runtime_error( "test" );
    } catch( const std::runtime_error & ) {}
    assert( !ds_hud::read().active && ds_hud::read().activity.text[11].empty() );
}

#if defined(__ANDROID__)
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_EnvironmentHudSnapshotTest_seed( JNIEnv *, jclass, jint which )
{
    ds_hud::end_session();
    if( which == 0 ) { return; }
    ds_hud::begin_session();
    if( which == 1 ) { return; }
    ds_hud::body_health hp;
    hp.current.fill( 30 );
    hp.maximum.fill( 80 );
    ds_hud::core_status core;
    core.strength = 5;
    core.dexterity = 0;
    core.intelligence = -2;
    core.perception = 3;
    core.speed = 55;
    core.focus = 137;
    core.movement_mode = "walk (W)";
    ds_hud::activity_status fields;
    fields.text = { "Fresh", "None", "|||||", "+ 0%", "", "Thursday, May 20",
                    "???", "road", "Clear", "bright", "Light Breeze \xe2\x86\x97", "-" };
    fields.available.fill( true );
    if( which == 3 ) {
        fields.text[6] = "08:12:34";
        fields.text[7] = std::string( 2000, 'x' ) + "\xf0\x9f\x8c\x8d" + std::string( 1, '\0' );
        fields.text[8] = "Rain";
        fields.text[9] = "dark";
        fields.text[11] = "-5\xc2\xb0" "C";
    }
    if( which == 4 ) {
        fields.available[8] = false;
        fields.text[8] = "must not leak";
    }
    ds_hud::publish( 23, 100, hp, core, fields );
}
#endif
