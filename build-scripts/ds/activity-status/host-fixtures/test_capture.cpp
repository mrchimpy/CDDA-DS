#include "game.h"
#include "widget.h"
#include "ds_hud.h"
#include <cassert>
int main() {
    game g;
    g.draw_panels( true );
    assert( total_renders == 0 && !ds_hud::read().active );
    ds_hud::session_scope scope;
    g.draw_panels( true );
    auto s = ds_hud::read();
    assert( s.ready && s.current == 35 && s.core.strength == 5 && s.core.focus == 140 );
    assert( s.core.movement_mode == "walk (W)" );
    for( int i = 0; i < 5; ++i ) {
        assert( s.activity.available[i] && s.activity.text[i] == std::to_string( i ) + ":0" );
        assert( definitions[i].renders == 0 ); // The shared definition was not modified.
    }
    g.u.sample = 9;
    missing_pain = true;
    g.draw_panels( false );
    s = ds_hud::read();
    assert( !s.activity.available[4] && s.activity.text[4].empty() );
    assert( s.activity.text[0] == "0:9" );
}
