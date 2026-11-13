#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <stdexcept>
#include <thread>

static ds_hud::activity_status status_for( int value )
{
    ds_hud::activity_status result;
    for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
        result.available[i] = true;
        result.text[i] = std::to_string( value ) + ":" + std::to_string( i );
    }
    return result;
}
static void assert_cleared( const ds_hud::snapshot &state )
{
    assert( !state.ready && state.current == 0 && state.maximum == 0 );
    assert( state.core.movement_mode.empty() && state.core.focus == 0 );
    for( std::size_t i = 0; i < ds_hud::activity_field_count; ++i ) {
        assert( !state.activity.available[i] && state.activity.text[i].empty() );
    }
    for( int i = 0; i < 6; ++i ) {
        assert( state.health.current[i] == 0 && state.health.maximum[i] == 0 );
    }
}
int main()
{
    using namespace ds_hud;
    end_session();
    publish( 1, 100, {}, {}, status_for( 1 ) );
    assert_cleared( read() );
    begin_session();
    assert( read().active );
    assert_cleared( read() );
    body_health health;
    health.current.fill( 20 );
    health.maximum.fill( 80 );
    core_status core;
    core.strength = -1;
    core.focus = 145;
    core.movement_mode = "walk (W)";
    activity_status activity = status_for( 7 );
    activity.text[4].clear(); // Blank pain is valid, not missing.
    activity.available[2] = false;
    publish( 35, 100, health, core, activity );
    auto result = read();
    assert( result.ready && result.age_ms >= 0 );
    assert( result.activity.available[4] && result.activity.text[4].empty() );
    assert( !result.activity.available[2] );
    const auto wire = wire_values( result );
    assert( wire.size() == 29 && wire[18] == -1 && wire[23] == 145 );
    assert( wire[24] == 1 && wire[26] == 0 && wire[28] == 1 );
    activity.text[0] = "caller mutation";
    result.activity.text[1] = "reader mutation";
    assert( read().activity.text[0] == "7:0" && read().activity.text[1] == "7:1" );
    publish( -1, 100, health, core, activity );
    assert_cleared( read() );
    publish( 0, 0, health, core, activity );
    assert_cleared( read() );
    end_session();
    try {
        session_scope scope;
        publish( 2, 100, health, core, activity );
        throw std::runtime_error( "test" );
    } catch( const std::runtime_error & ) {}
    assert( !read().active );
    assert_cleared( read() );
    {
        session_scope scope;
        std::atomic<bool> done{ false };
        std::thread writer( [&]() {
            for( int n = 1; n <= 10000; ++n ) {
                body_health h;
                h.current.fill( n );
                h.maximum.fill( 20000 );
                core_status c;
                c.focus = n;
                c.movement_mode = std::to_string( n );
                publish( n, 20000, h, c, status_for( n ) );
            }
            done = true;
        } );
        do {
            const snapshot s = read();
            if( !s.ready ) continue;
            assert( s.current == s.health.current[5] && s.current == s.core.focus );
            assert( s.core.movement_mode == std::to_string( s.current ) );
            for( std::size_t i = 0; i < activity_field_count; ++i ) {
                assert( s.activity.available[i] );
                assert( s.activity.text[i] == std::to_string( s.current ) + ":" + std::to_string( i ) );
            }
        } while( !done.load() );
        writer.join();
    }
    assert_cleared( read() );
    begin_session();
    assert_cleared( read() );
    end_session();
}
