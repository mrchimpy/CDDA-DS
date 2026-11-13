#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <string>
#include <thread>

static void publish_test_state( int version )
{
    ds_hud::body_health health;
    ds_hud::core_status core;
    ds_hud::activity_status details;
    for( int i = 0; i < 6; ++i ) {
        health.current[i] = 10 + i;
        health.maximum[i] = 100 + i;
    }
    core.strength = -2;
    core.dexterity = 0;
    core.intelligence = 8;
    core.perception = 9;
    core.speed = 75;
    core.focus = 137;
    core.movement_mode = "walk (W)";
    for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
        details.available[i] = true;
        details.text[i] = "slot " + std::to_string( i );
    }
    details.text[17] = "Comfortable";
    details.text[18] = "(Rising!)";
    details.text[19] = "|||..";
    details.text[20] = "helmet";
    details.text[21] = std::string( 500, 'x' ) + " \xE2\x86\x91 \xF0\x9F\x98\x80";
    details.text[22] = std::string( "a\0b", 3 );
    details.text[23] = "gloves";
    details.text[24] = "jeans";
    details.text[25] = "boots";
    if( version == 1 ) {
        details.text[17] = "Chilly";
        details.text[18].clear();
        details.text[19].clear();
        details.available[20] = false;
        details.text[20].clear();
        details.text[21] = "jacket > 2 items";
        details.text[23].clear();
        details.text[25] = "sandals";
    }
    ds_hud::publish( 25, 100, health, core, details );
}

#if defined(__ANDROID__)
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_BodyDetailsSnapshotTest_seed( JNIEnv *, jclass, jint version )
{
    if( version == 2 ) {
        ds_hud::publish( 0, 0 );
    } else if( version == 3 ) {
        ds_hud::end_session();
    } else if( version == 4 ) {
        ds_hud::begin_session();
    } else {
        if( version == 0 ) {
            ds_hud::begin_session();
        }
        publish_test_state( version );
    }
}
#else
int main()
{
    static_assert( ds_hud::activity_field_count == 26, "Widget count" );
    static_assert( ds_hud::wire_field_count == 50, "Wire count" );
    ds_hud::end_session();
    publish_test_state( 0 );
    assert( !ds_hud::read().ready );
    ds_hud::begin_session();
    publish_test_state( 0 );
    auto first = ds_hud::read();
    assert( first.ready && first.activity.text[20] == "helmet" );
    const auto packed = ds_hud::wire_values( first );
    assert( packed[18] == -2 && packed[23] == 137 && packed[49] == 1 );
    first.activity.text[20] = "changed reader copy";
    assert( ds_hud::read().activity.text[20] == "helmet" );
    publish_test_state( 1 );
    const auto changed = ds_hud::read();
    assert( changed.activity.text[17] == "Chilly" );
    assert( changed.activity.available[19] && changed.activity.text[19].empty() );
    assert( !changed.activity.available[20] && changed.activity.text[20].empty() );
    ds_hud::publish( 0, 0 );
    for( bool available : ds_hud::read().activity.available ) {
        assert( !available );
    }
    std::atomic<bool> done{ false };
    std::thread writer( [&done]() {
        for( int v = 1; v <= 3000; ++v ) {
            ds_hud::body_health health;
            ds_hud::core_status core;
            ds_hud::activity_status details;
            core.speed = v;
            core.movement_mode = std::to_string( v );
            for( int &hp : health.current ) {
                hp = v;
            }
            for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
                details.available[i] = v % 2 == 0;
                details.text[i] = std::to_string( v );
            }
            ds_hud::publish( v, 10000, health, core, details );
            details.text[25] = "mutated caller";
        }
        done = true;
    } );
    do {
        const auto s = ds_hud::read();
        if( !s.ready ) {
            continue;
        }
        assert( s.core.speed == s.current );
        assert( s.core.movement_mode == std::to_string( s.current ) );
        for( int hp : s.health.current ) {
            assert( hp == s.current );
        }
        for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
            assert( s.activity.text[i] == std::to_string( s.current ) );
            assert( s.activity.available[i] == ( s.current % 2 == 0 ) );
        }
    } while( !done );
    writer.join();
    ds_hud::end_session();
    auto cleared = ds_hud::read();
    assert( !cleared.active && !cleared.ready );
    for( const auto &text : cleared.activity.text ) {
        assert( text.empty() );
    }
    ds_hud::begin_session();
    assert( ds_hud::read().active && !ds_hud::read().ready );
    publish_test_state( 0 );
    assert( ds_hud::read().activity.text[25] == "boots" );
    ds_hud::end_session();
}
#endif
