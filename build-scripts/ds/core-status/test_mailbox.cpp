#include "ds_hud.h"
#include <atomic>
#include <cassert>
#include <stdexcept>
#include <thread>

static ds_hud::core_status fields( int seed )
{
    return { seed, seed + 1, seed + 2, seed + 3, seed + 4, seed + 5,
             "mode-" + std::to_string( seed ) };
}

static ds_hud::body_health limbs( int seed )
{
    ds_hud::body_health result;
    for( int i = 0; i < 6; ++i ) {
        result.current[i] = seed + i;
        result.maximum[i] = seed + i + 100;
    }
    return result;
}

int main()
{
    ds_hud::end_session();
    auto before = ds_hud::read();
    ds_hud::publish( 1, 100, limbs( 1 ), fields( 1 ) );
    assert( !ds_hud::read().active && ds_hud::read().sequence == before.sequence );
    {
        ds_hud::session_scope session;
        assert( ds_hud::read().active && !ds_hud::read().ready );
        auto health = limbs( 11 );
        auto core = fields( 11 );
        ds_hud::publish( 11, 1011, health, core );
        health.current[0] = -999;
        core.movement_mode = "changed after publish";
        auto copy = ds_hud::read();
        assert( copy.health.current[0] == 11 && copy.core.movement_mode == "mode-11" );
        copy.core.strength = -999;
        copy.core.movement_mode = "mutated reader copy";
        assert( ds_hud::read().core.strength == 11 );
        assert( ds_hud::read().core.movement_mode == "mode-11" );
        auto wire = ds_hud::wire_values( ds_hud::read() );
        assert( wire.size() == 24 && wire[0] == 1 && wire[1] == 1 );
        assert( wire[2] == 11 && wire[3] == 1011 );
        for( int i = 0; i < 6; ++i ) {
            assert( wire[6 + i * 2] == 11 + i );
            assert( wire[7 + i * 2] == 111 + i );
            assert( wire[18 + i] == 11 + i );
        }
        assert( ds_hud::read().age_ms >= 0 );
        // Values are current readings, not percentages or clamped nominal values.
        ds_hud::publish( 0, 100, {}, { 0, -1, 250, 4, 37, 200, "prone (P)" } );
        copy = ds_hud::read();
        assert( copy.ready && copy.core.dexterity == -1 && copy.core.focus == 200 );
        ds_hud::publish( -1, 100, limbs( 5 ), fields( 5 ) );
        copy = ds_hud::read();
        assert( !copy.ready && copy.health.current[0] == 0 );
        assert( copy.core.strength == 0 && copy.core.movement_mode.empty() );
        ds_hud::publish( 1, 0, limbs( 5 ), fields( 5 ) );
        assert( !ds_hud::read().ready );
    }
    auto cleared = ds_hud::read();
    assert( !cleared.active && !cleared.ready && cleared.current == 0 );
    for( int i = 0; i < 6; ++i ) assert( cleared.health.current[i] == 0 );
    assert( cleared.core.movement_mode.empty() && cleared.core.focus == 0 );
    try {
        ds_hud::session_scope session;
        ds_hud::publish( 4, 100, limbs( 4 ), fields( 4 ) );
        throw std::runtime_error( "test unwind" );
    } catch( const std::runtime_error & ) { }
    assert( !ds_hud::read().active && ds_hud::read().core.movement_mode.empty() );

    ds_hud::begin_session();
    std::atomic<bool> done{ false };
    std::atomic<int> reads{ 0 };
    std::thread reader( [&] {
        do {
            const auto state = ds_hud::read();
            if( state.ready ) {
                const int seed = state.current;
                assert( state.maximum == seed + 1000 );
                const auto w = ds_hud::wire_values( state );
                for( int i = 0; i < 6; ++i ) {
                    assert( w[18 + i] == seed + i );
                    assert( state.health.current[i] == seed + i );
                    assert( state.health.maximum[i] == seed + i + 100 );
                }
                assert( state.core.movement_mode == "mode-" + std::to_string( seed ) );
            }
            ++reads;
        } while( !done );
    } );
    for( int seed = 1; seed <= 20000; ++seed ) {
        ds_hud::publish( seed, seed + 1000, limbs( seed ), fields( seed ) );
    }
    done = true;
    reader.join();
    assert( reads > 0 );
    ds_hud::end_session();
    assert( ds_hud::read().core.movement_mode.empty() );
    ds_hud::begin_session();
    assert( ds_hud::read().active && !ds_hud::read().ready );
    assert( ds_hud::read().core.strength == 0 );
    ds_hud::end_session();
}
