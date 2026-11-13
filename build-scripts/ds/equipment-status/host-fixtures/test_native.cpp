#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <stdexcept>
#include <string>
#include <thread>

static_assert( ds_hud::activity_field_count == 17, "Equipment text protocol" );
static_assert( ds_hud::wire_field_count == 41, "Equipment numeric protocol" );

static void seed( int scenario )
{
    if( scenario == 0 ) {
        ds_hud::end_session();
        return;
    }
    ds_hud::begin_session();
    if( scenario == 3 ) {
        return;
    }
    ds_hud::body_health health;
    for( int i = 0; i < 6; ++i ) {
        health.current[i] = 20 + i;
        health.maximum[i] = 80 + i;
    }
    ds_hud::core_status core;
    core.strength = 5;
    core.dexterity = 0;
    core.intelligence = -1;
    core.perception = 4;
    core.speed = 75;
    core.focus = 137;
    core.movement_mode = "walk (W)";
    ds_hud::activity_status status;
    const char *values[] = {
        "Fresh", "None", "|||||", "+ 0%", "", "Thursday, May 20", "Morning",
        "road", "Clear", "bright", "Light Breeze", "-",
        "fists", "No style", "--", "0", ":|"
    };
    for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
        status.text[i] = values[i];
        status.available[i] = true;
    }
    if( scenario == 2 ) {
        status.text[12] = std::string( 512, 'x' ) + u8" / epee \u2694 \U0001f9ed" + std::string( "\0tail", 5 );
        status.text[13] = "Karate";
        status.text[14] = "2.50 kJ";
        status.text[15] = "99";
        status.text[16] = ":)";
    } else if( scenario == 4 ) {
        status.text[12].clear();
        status.available[13] = false;
        status.text[13].clear();
        status.text[14] = "0 J";
        status.text[16].clear();
    }
    ds_hud::publish( scenario == 5 ? -1 : 25, 100, health, core, status );
}

#if defined(__ANDROID__)
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_EquipmentHudSnapshotTest_seed( JNIEnv *, jclass, jint scenario )
{
    seed( scenario );
}
#else
int main()
{
    seed( 1 );
    auto saved = ds_hud::read();
    assert( saved.ready && saved.activity.text[12] == "fists" );
    auto copy = saved;
    copy.activity.text[12] = "different";
    copy.activity.available[13] = false;
    assert( ds_hud::read().activity.text[12] == "fists" );
    assert( ds_hud::read().activity.available[13] );
    seed( 2 );
    assert( saved.activity.text[12] == "fists" );
    assert( ds_hud::read().activity.text[12].size() > 512 );
    seed( 5 );
    assert( !ds_hud::read().ready && ds_hud::read().activity.text[12].empty() );
    seed( 0 );
    ds_hud::publish( 20, 100, {}, {}, saved.activity );
    assert( !ds_hud::read().active && !ds_hud::read().ready );
    try {
        ds_hud::session_scope session;
        ds_hud::publish( 20, 100, {}, {}, saved.activity );
        throw std::runtime_error( "fixture" );
    } catch( const std::runtime_error & ) {
    }
    for( const auto &text : ds_hud::read().activity.text ) {
        assert( text.empty() );
    }
    std::atomic<bool> finished{ false };
    {
        ds_hud::session_scope session;
        std::thread writer( [&] {
            for( int n = 1; n <= 3000; ++n ) {
                ds_hud::body_health health;
                health.current.fill( n );
                health.maximum.fill( 4000 );
                ds_hud::core_status core;
                core.strength = n;
                core.movement_mode = std::to_string( n );
                ds_hud::activity_status status;
                status.text.fill( std::to_string( n ) );
                status.available.fill( n % 2 != 0 );
                ds_hud::publish( n, 4000, health, core, status );
            }
            finished = true;
        } );
        do {
            const auto state = ds_hud::read();
            if( !state.ready ) {
                continue;
            }
            const auto packed = ds_hud::wire_values( state );
            assert( state.current == state.core.strength );
            assert( state.current == state.health.current[5] );
            assert( state.core.movement_mode == std::to_string( state.current ) );
            for( std::size_t i = 0; i < 17; ++i ) {
                assert( state.activity.text[i] == state.core.movement_mode );
                assert( state.activity.available[i] == ( state.current % 2 != 0 ) );
                assert( packed[24 + i] == state.activity.available[i] );
            }
        } while( !finished );
        writer.join();
    }
    const auto cleared = ds_hud::read();
    assert( !cleared.active && !cleared.ready && cleared.core.movement_mode.empty() );
    for( std::size_t i = 0; i < 17; ++i ) {
        assert( cleared.activity.text[i].empty() && !cleared.activity.available[i] );
    }
}
#endif
