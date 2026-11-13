#pragma once
#include "game.h"
#include <array>
#include <cassert>
#include <string>
inline int total_renders = 0;
struct widget {
    int index;
    int renders = 0;
    std::string show( const avatar &u, unsigned int width ) {
        assert( width == 80 );
        ++renders;
        ++total_renders;
        return "<color_white>" + std::to_string( index ) + ":" + std::to_string( u.sample ) + "</color>";
    }
};
inline std::array<widget, 5> definitions = {{{0,0}, {1,0}, {2,0}, {3,0}, {4,0}}};
inline bool missing_pain = false;
struct widget_id {
    int index = -1;
    explicit widget_id( const char *name ) {
        const char *ids[] = { "weariness_desc", "activity_desc", "weariness_transition_graph",
                              "weary_malus_desc", "pain_desc_label" };
        for( int i = 0; i < 5; ++i ) if( std::string( name ) == ids[i] ) index = i;
    }
    bool is_valid() const { return index >= 0 && !( missing_pain && index == 4 ); }
    const widget &obj() const { assert( is_valid() ); return definitions[index]; }
};
inline std::string remove_color_tags( std::string value ) {
    const std::string opening = "<color_white>", closing = "</color>";
    assert( value.find( opening ) == 0 );
    return value.substr( opening.size(), value.size() - opening.size() - closing.size() );
}
