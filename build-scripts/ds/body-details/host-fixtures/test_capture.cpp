#include "widget.h"
#include "ds_hud.h"

int main()
{
    const char *ids[] = { /* WIDGET_IDS */ };
    for( const char *id : ids ) {
        definitions[id].value = id;
    }
    widget &gate = definitions["oxygen_classic_layout"];
    gate.children.emplace_back( "oxygen_graph_classic" );
    game g;
    g.draw_panels( true );
    assert( !ds_hud::read().ready && total_calls == 0 && gate_calls == 0 );
    ds_hud::session_scope session;
    g.draw_panels( true );
    auto s = ds_hud::read();
    assert( s.ready && s.core.focus == 137 && total_calls == 26 && gate_calls == 1 );
    for( int i = 0; i < 26; ++i ) {
        assert( s.activity.available[i] && s.activity.text[i] == ids[i] );
        assert( definitions.at( ids[i] ).calls == 0 );
    }
    assert( gate.calls == 0 ); // Even conditional selection operates on a copy.
    definitions.at( "body_temp_desc_label" ).value = "Chilly";
    definitions.at( "body_temp_delta_desc_label" ).value = "(Falling)";
    definitions.at( "bp_armor_outer_torso_text" ).value = "jacket > 2 items";
    definitions.at( "bp_armor_outer_hands_text" ).value.clear();
    definitions.at( "oxygen_graph_classic" ).value = "|....";
    g.draw_panels( true );
    s = ds_hud::read();
    assert( s.activity.text[17] == "Chilly" && s.activity.text[18] == "(Falling)" );
    assert( s.activity.text[19] == "|...." );
    assert( s.activity.text[21] == "jacket > 2 items" );
    assert( s.activity.available[23] && s.activity.text[23].empty() );
    gate.children.clear(); // Native layout's full-capacity case is valid blank.
    const int calls_before = total_calls;
    g.draw_panels( true );
    s = ds_hud::read();
    assert( s.activity.available[19] && s.activity.text[19].empty() );
    assert( total_calls == calls_before + 25 );
    gate.children.emplace_back( "unsupported_custom_widget" );
    g.draw_panels( true );
    assert( !ds_hud::read().activity.available[19] );
    gate.children = { widget_id( "oxygen_graph_classic" ), widget_id( "extra" ) };
    g.draw_panels( true );
    assert( !ds_hud::read().activity.available[19] );
    gate.children = { widget_id( "oxygen_graph_classic" ) };
    definitions.erase( "oxygen_graph_classic" );
    g.draw_panels( true );
    assert( !ds_hud::read().activity.available[19] );
    definitions["oxygen_graph_classic"].value = "||...";
    definitions.erase( "oxygen_classic_layout" );
    g.draw_panels( true );
    assert( !ds_hud::read().activity.available[19] );
    definitions.erase( "bp_armor_outer_head_text" );
    definitions.at( "body_temp_desc_label" ).value.clear();
    g.draw_panels( true );
    s = ds_hud::read();
    assert( !s.activity.available[20] && s.activity.text[20].empty() );
    assert( s.activity.available[17] && s.activity.text[17].empty() );
    auto &restored_gate = definitions["oxygen_classic_layout"];
    restored_gate.children.emplace_back( "oxygen_graph_classic" );
    g.draw_panels( true );
    assert( ds_hud::read().activity.text[19] == "||..." );
    ds_hud::end_session();
    const int ended_calls = total_calls;
    g.draw_panels( true );
    assert( !ds_hud::read().ready && total_calls == ended_calls );
    for( const auto &value : ds_hud::read().activity.text ) {
        assert( value.empty() );
    }
    ds_hud::begin_session();
    assert( !ds_hud::read().ready );
    g.draw_panels( true );
    assert( ds_hud::read().activity.text[19] == "||..." );
}
