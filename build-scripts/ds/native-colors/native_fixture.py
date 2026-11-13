"""Compile the real native color evaluator with substitute game objects.

The JSON expression engine and full gameplay simulation are not reproduced here.
"""
from pathlib import Path
import hashlib
import json

VALUE_COLOR_SHA256 = '7204551ef61ab36243206b93fd9edaa79cc72912f378510ff519bc97d428561f'


def function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


HEADER = r'''#pragma once
#include <algorithm>
#include <array>
#include <climits>
#include <cmath>
#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <utility>
#include <vector>
struct nc_color {
 int pair = 99; bool bright = false, background_bright = false;
 int to_color_pair_index() const { return pair; }
 bool is_bold() const { return bright; }
 bool is_blink() const { return background_bright; }
 bool operator==(const nc_color &o) const {return pair==o.pair&&bright==o.bright&&background_bright==o.background_bright;}
 bool operator!=(const nc_color &o) const {return !(*this==o);}
};
inline const nc_color c_unset{}, c_light_gray{1,false,false},c_dark_gray{30,true,false},c_white{1,true,false};
namespace cata_cursesport {
struct pairs { int FG=0, BG=0; };
inline std::array<pairs,100> colorpairs{};
}
struct SDL_Color {std::uint8_t r,g,b,a;};
inline std::array<SDL_Color,16> windowsPalette{};
inline std::map<std::string,nc_color> named_colors;
enum class report_color_error {no,yes};
struct color_tag_parse_result {
 enum tag_type {open_color_tag,close_color_tag,non_color_tag};
 tag_type type; nc_color color;
};
inline color_tag_parse_result get_color_from_tag(std::string_view s,report_color_error) {
 if(s=="</color>")return {color_tag_parse_result::close_color_tag,{}};
 if(s.substr(0,7)!="<color_"||s.back()!='>')return {color_tag_parse_result::non_color_tag,{}};
 std::string name(s.substr(7,s.size()-8));
 if(name.substr(0,2)=="c_")name=name.substr(2);
 auto found=named_colors.find(name);
 return found==named_colors.end()?color_tag_parse_result{color_tag_parse_result::non_color_tag,{}}:
  color_tag_parse_result{color_tag_parse_result::open_color_tag,found->second};
}
struct avatar {};
struct widget {
 int _var_min=0,_var_max=100,value=100;
 std::pair<int,int> _var_norm={INT_MIN,INT_MAX};
 std::vector<nc_color> _colors;
 std::vector<int> _breaks;
 std::string marked;
 void set_default_var_range(const avatar &) {} // Explicit scenario-provided ranges.
 int get_var_value(const avatar &) const {return value;}
 std::string show(const avatar &,unsigned int) {return marked;}
 nc_color value_color(int value);
};
inline std::map<std::string,widget> definitions;
struct widget_id {
 std::string name;
 explicit widget_id(const char *n):name(n){}
 bool is_valid() const {return definitions.count(name)!=0;}
 widget obj() const {return definitions.at(name);}
};
void initialize_fixture();
'''


def write(root: Path, repository: Path) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    (root / 'fixture.h').write_text(HEADER)
    for name in ['avatar.h','color.h','cursesport.h','sdltiles.h','widget.h']:
        (root / name).write_text('#include "fixture.h"\n')
    source = (repository / 'src/widget.cpp').read_text()
    body = function_body(source, 'nc_color widget::value_color( int value )')
    actual = hashlib.sha256(body.encode()).hexdigest()
    if actual != VALUE_COLOR_SHA256:
        raise AssertionError('Pinned native value_color implementation changed: ' + actual)
    objects = {}
    for path in (repository / 'data/json/ui').glob('*.json'):
        for item in json.loads(path.read_text()):
            if isinstance(item,dict) and isinstance(item.get('id'),str): objects[item['id']] = item

    def resolve(name: str) -> dict:
        item = objects[name]
        return {**(resolve(item['copy-from']) if 'copy-from' in item else {}), **item}

    names = ['stamina_graph_classic','hp_head_graph_no_label','hp_torso_graph_no_label',
             'hp_left_arm_graph_no_label','hp_right_arm_graph_no_label','hp_left_leg_graph_no_label',
             'hp_right_leg_graph_no_label','str_num','dex_num','int_num','per_num','speed_num','focus_num']
    lines = [ '#include "fixture.h"', body, 'void initialize_fixture() {',
              'definitions.clear(); named_colors.clear();' ]
    palette = json.loads((repository / 'data/raw/colors.json').read_text())[0]
    keys = ['BLACK','RED','GREEN','BROWN','BLUE','MAGENTA','CYAN','GRAY','DGRAY','LRED','LGREEN','YELLOW','LBLUE','LMAGENTA','LCYAN','WHITE']
    for i,key in enumerate(keys):
        lines.append('windowsPalette[%d] = {%s,255};' % (i,','.join(map(str,palette[key]))))
    # Fixture maps standard color names to the same native pair+bright representation.
    colors = [('black',0,False),('red',1,False),('green',2,False),('brown',3,False),
              ('blue',4,False),('magenta',5,False),('cyan',6,False),('light_gray',7,False),
              ('dark_gray',0,True),('light_red',1,True),('light_green',2,True),('yellow',3,True),
              ('light_blue',4,True),('pink',5,True),('light_cyan',6,True),('white',7,True)]
    for name,index,bright in colors:
        pair = 1 if index==7 else 30 if index==0 else index+1
        lines.append('cata_cursesport::colorpairs[%d] = {%d,0};' % (pair,index))
        lines.append('named_colors["%s"]={%d,%s,false};' % (name,pair,str(bright).lower()))
    lines += ['cata_cursesport::colorpairs[40]={5,1}; named_colors["magenta_red"]={40,false,false};',
              'cata_cursesport::colorpairs[41]={1,1}; named_colors["red_red"]={41,false,false};']
    for name in names:
        obj = resolve(name)
        cols = ','.join('named_colors.at('+json.dumps(c.removeprefix('c_'))+')' for c in obj['colors'])
        lines.append('definitions[%s]._colors = {%s};' % (json.dumps(name),cols))
    for name in ['str_num','dex_num','int_num','per_num']:
        lines.append('definitions["%s"]._var_min=7; definitions["%s"]._var_max=13; definitions["%s"]._var_norm={10,10}; definitions["%s"].value=10;' % (name,name,name,name))
    lines += ['definitions["speed_num"]._var_max=200; definitions["speed_num"]._var_norm={100,100};',
              'definitions["focus_num"]._var_max=200; definitions["focus_num"]._var_norm={90,110};']
    for name in ['bodypart_head_status_text','bodypart_torso_status_text','bodypart_larm_status_text',
                 'bodypart_rarm_status_text','bodypart_lleg_status_text','bodypart_rleg_status_text']:
        lines.append('definitions["%s"].marked="BODY";' % name)
    lines += ['definitions["move_mode_letter"].marked="<color_white>W</color>";', '}']
    destination = root/'fixture.cpp'; destination.write_text('\n'.join(lines)+'\n')
    return [destination]
