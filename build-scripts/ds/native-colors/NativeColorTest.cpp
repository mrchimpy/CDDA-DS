#include "ds_hud.h"
#include "ds_hud_color_capture.h"
#include <atomic>
#include <cassert>
#include <iostream>
#include <thread>

using namespace ds_hud;

static std::uint32_t fg( const char *name )
{
    return native_ink( named_colors.at( name ) ).foreground;
}

static void parser_test()
{
    initialize_fixture();
    const ink normal = native_ink( c_light_gray );
    const auto text = native_styled_text( "a<color_red>b<color_green>c</color>d</color>e", normal );
    assert( text.valid && text.text == "abcde" && text.runs.size() == 5 );
    assert( text.runs[1].color.foreground == fg( "red" ) );
    assert( text.runs[2].color.foreground == fg( "green" ) );
    assert( text.runs[3].color.foreground == fg( "red" ) );
    assert( text.runs[4].color == normal );
    const auto unicode = native_styled_text( "<color_yellow>\xE2\x86\x91\xF0\x9F\x98\x80</color>!", normal );
    assert( unicode.text.size() == 8 && unicode.runs[0].end == 7 && unicode.runs[1].begin == 7 );
    const auto literal = native_styled_text( "<item> < <color_red>X</color>\n</color>Y", normal );
    assert( literal.text == "<item> < X\nY" );
    const auto empty = native_styled_text( "<color_green></color>", normal );
    assert( empty.valid && empty.text.empty() && empty.runs.empty() );
    assert( native_styled_text( "<color_invalid>x</color>", normal ).text == "<color_invalid>x" );
    std::string nested;
    for( int i = 0; i < 257; ++i ) { nested += "<color_red>"; }
    assert( !native_styled_text( nested, normal ).valid );
    assert( !native_styled_text( std::string( color_text_limit + 1, 'x' ), normal ).valid );
    const auto unfinished = native_styled_text( "a<color_red", normal );
    assert( unfinished.text == "a<color_red" );
}

static void threshold_test()
{
    initialize_fixture();
    avatar u;
    widget &hp = definitions.at( "hp_head_graph_no_label" );
    hp._var_max = 800;
    const std::pair<int,const char *> checks[] = {
        {-1,"red"},{0,"red"},{99,"red"},{100,"light_red"},{299,"light_red"},
        {300,"yellow"},{499,"yellow"},{500,"light_green"},{699,"light_green"},
        {700,"green"},{800,"green"},{900,"green"}
    };
    for( auto check : checks ) {
        hp.value = check.first;
        const auto colors = capture_native_colors( u );
        assert( colors.scalars[1].foreground == fg( check.second ) );
    }
    const char *expected[] = {"red","red","light_red","yellow","white","light_cyan","light_green","green","green"};
    for( const char *id : {"str_num","dex_num","int_num","per_num"} ) {
        for( int value = 6; value <= 14; ++value ) {
            definitions.at(id).value = value;
            color_status c;
            assert( native_number_ink( u,id,c ).foreground == fg( expected[value-6] ) );
        }
    }
    const std::pair<int,const char *> focus[] = {{0,"red"},{33,"red"},{34,"light_red"},
        {89,"light_red"},{90,"white"},{110,"white"},{111,"light_green"},{166,"light_green"},{167,"green"},{200,"green"}};
    for( auto check : focus ) {
        definitions.at("focus_num").value = check.first;
        color_status c;
        assert( native_number_ink(u,"focus_num",c).foreground == fg(check.second) );
    }
    // The real native algorithm, including explicit breaks, degenerate ranges,
    // clamping and the normal override, is compiled from pinned widget.cpp.
    widget custom; custom._colors={named_colors.at("red"),named_colors.at("green")};
    custom._breaks={30}; custom._var_norm={0,100};
    assert( custom.value_color(29)==named_colors.at("red") );
    assert( custom.value_color(30)==named_colors.at("green") );
    custom._breaks.clear(); custom._var_max=0;
    assert( custom.value_color(0)==named_colors.at("red") );
}

static void palette_test()
{
    initialize_fixture(); avatar u;
    assert( fg("green")==0xff006e00u && fg("light_green")==0xff00ff00u );
    assert( fg("light_red")==0xffff9696u );
    definitions.at("bodypart_head_status_text").marked="<color_magenta_red>HEAD</color>";
    auto colors=capture_native_colors(u);
    assert( colors.scalars[7].foreground==0xff8b3a62u && colors.scalars[7].background==0xffff0000u );
    // A label condition is independent of the HP color.
    assert( colors.scalars[1].foreground==fg("green") );
    windowsPalette[2]={1,2,3,255}; windowsPalette[1]={4,5,6,255};
    colors=capture_native_colors(u);
    assert( colors.scalars[1].foreground==0xff010203u && colors.scalars[7].background==0xff040506u );
    nc_color bright_bg{40,false,true};
    assert( native_ink(bright_bg).background==0xffff9696u );
    definitions.erase("str_num"); colors=capture_native_colors(u);
    assert( !colors.complete && colors.scalars[13]==colors.neutral );
}

static void mailbox_test()
{
    initialize_fixture(); begin_session();
    body_health health; health.current[0]=3; health.maximum[0]=100;
    activity_status activity; activity.text[0]="red"; activity.available[0]=true;
    auto colors=capture_native_colors(avatar{});
    colors.runs[0]={{0,3,{0xffff0000u,0xff000000u}}};
    publish(40,100,health,{},activity,colors);
    colors.runs[0][0].color.foreground=0; activity.text[0]="changed";
    auto state=read(); assert(state.colors.runs[0][0].color.foreground==0xffff0000u);
    state.colors.runs[0].clear(); assert(read().colors.runs[0].size()==1);
    assert(read().activity.text[0]=="red");
    auto words=pack_colors(read().colors,read().sequence);
    assert(words[0]==0x44534331 && words[2]==static_cast<std::int64_t>(read().sequence));
    publish(0,0,health,{},activity,colors);assert(!read().colors.ready);
    end_session();assert(!read().active && read().colors.runs[0].empty());
    begin_session();assert(!read().ready && !read().colors.ready);
    std::atomic<bool> done{false};std::atomic<int> failures{0};
    std::thread reader([&]{
        while(!done.load()) {
            auto snap=read();
            if(snap.ready && snap.colors.scalars[0].foreground!=(0xff000000u|snap.current))++failures;
        }
    });
    for(int i=1;i<2000;++i){
        color_status c;c.ready=true;c.scalars[0].foreground=0xff000000u|(i%200);
        publish(i%200,200,{}, {}, {},c);
    }
    done=true;reader.join();assert(failures==0);end_session();
}

#if defined(__ANDROID__)
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_cleverraven_cataclysmdda_NativeColorHostTest_seed(JNIEnv *,jclass,jint mode)
{
    end_session();
    if(mode==0)return;
    initialize_fixture();begin_session();
    if(mode==3)return; // Active but not ready.
    avatar u;body_health health;core_status core;activity_status activity;
    for(int i=0;i<6;++i){health.current[i]=(i+1)*10;health.maximum[i]=100;}
    core.strength=10;core.dexterity=8;core.intelligence=7;core.perception=12;core.speed=80;core.focus=45;
    const char *stats[]={"str_num","dex_num","int_num","per_num","speed_num","focus_num"};
    if(mode==6){core.dexterity=10;core.intelligence=10;core.perception=10;core.speed=100;core.focus=100;}
    const int values[]={core.strength,core.dexterity,core.intelligence,core.perception,core.speed,core.focus};
    for(int i=0;i<6;++i)definitions.at(stats[i]).value=values[i];
    const char *parts[]={"hp_head_graph_no_label","hp_torso_graph_no_label","hp_left_arm_graph_no_label", "hp_right_arm_graph_no_label","hp_left_leg_graph_no_label","hp_right_leg_graph_no_label"};
    for(int i=0;i<6;++i)definitions.at(parts[i]).value=health.current[i];
    const int stamina=mode==2?0:mode==6?100:mode==7?1249:50;
    const int maximum=mode==7?10000:100;
    definitions.at("stamina_graph_classic").value=stamina;
    definitions.at("stamina_graph_classic")._var_max=maximum;
    if(mode==2){health.current[0]=0;definitions.at("hp_head_graph_no_label").value=0;}
    core.movement_mode="run (R)";definitions.at("move_mode_letter").marked="<color_red>R</color>";
    if(mode!=6)definitions.at("bodypart_head_status_text").marked="<color_magenta_red>HEAD</color>";
    if(mode==6){core.movement_mode="walk (W)";definitions.at("move_mode_letter").marked="<color_white>W</color>";}
    auto colors=capture_native_colors(u);
    for(std::size_t i=0;i<activity_field_count;++i){
        activity.available[i]=true;
        std::string marked="<color_yellow>value"+std::to_string(i)+"</color>";
        if(i==0)marked="<color_green>Fresh</color>";
        if(i==17)marked="<color_green>Comfortable</color>";
        if(i==18)marked="<color_blue>(Falling!!)</color>";
        if(i==20)marked="<color_green>++ </color><color_light_gray>Jacket </color><color_red>\xF0\x9F\x98\x80</color>";
        if(mode==4)marked="<color_green></color>";
        const auto s=native_styled_text(marked,colors.neutral);
        activity.text[i]=s.text;colors.runs[i]=s.runs;
    }
    if(mode==5){colors.neutral={0xff123456u,0xff010203u}; colors.scalars[0]={0xffabcdefu,0xff111111u};}
    publish(stamina,maximum,health,core,activity,colors);
}
#else
int main(int argc,char **argv)
{
    assert(argc==2);std::string mode=argv[1];
    if(mode=="parser")parser_test();
    else if(mode=="thresholds")threshold_test();
    else if(mode=="palette")palette_test();
    else if(mode=="mailbox")mailbox_test();
    else return 2;
    std::cout<<"native color test passed: "<<mode<<'\n';
}
#endif
