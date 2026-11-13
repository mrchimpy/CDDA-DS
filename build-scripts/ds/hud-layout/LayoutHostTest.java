package com.cleverraven.cataclysmdda;

import android.app.Presentation;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Display;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Production UI/decoder against host API substitutes; no device or renderer claim. */
public final class LayoutHostTest {
    private static final String[] PARTS = {"Head", "Torso", "Left arm", "Right arm", "Left leg", "Right leg"};
    private static final int[] DISPLAY_ORDER = {4,19,15,26,27,28,16,0,1,2,3,17,18,14,20,21,22,23,24,25};
    private static final int[] CORE_ORDER = {4,5,0,1,2,3};

    static void check(boolean value, String why) {
        if (!value) throw new AssertionError(why);
    }
    static Object field(Object o, String name) throws Exception {
        Field f=o.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(o);
    }
    static void call(Object o, String name, Class<?> type, Object value) throws Exception {
        Method m=o.getClass().getDeclaredMethod(name,type); m.setAccessible(true); m.invoke(o,value);
    }
    static List<View> descendants(View root) {
        List<View> result=new ArrayList<>();result.add(root);
        if(root instanceof ViewGroup) for(View v:((ViewGroup)root).children)result.addAll(descendants(v));
        return result;
    }
    static List<TextView> texts(View root) {
        List<TextView> result=new ArrayList<>();
        for(View v:descendants(root))if(v instanceof TextView)result.add((TextView)v);
        return result;
    }
    static List<LinearLayout> pairs(View root) {
        List<LinearLayout> result=new ArrayList<>();
        for(View v:descendants(root))if(v.getClass().getSimpleName().equals("StablePairRow"))result.add((LinearLayout)v);
        return result;
    }
    static void measure(View row,int width,int mode) {
        row.measure(View.MeasureSpec.makeMeasureSpec(width,mode),View.MeasureSpec.makeMeasureSpec(0,View.MeasureSpec.UNSPECIFIED));
    }
    static Object[] snapshot() {
        long[] n=new long[53];n[0]=1;n[1]=1;n[2]=640;n[3]=1000;n[4]=13;n[5]=125;
        for(int i=0;i<6;i++){n[6+2*i]=10*(i+1);n[7+2*i]=100;}
        for(int i=0;i<6;i++)n[18+i]=11+i;
        byte[][] t=new byte[30][];t[0]="walk (W)".getBytes(StandardCharsets.UTF_8);
        for(int i=0;i<29;i++){n[24+i]=1;t[i+1]=("field "+i).getBytes(StandardCharsets.UTF_8);}
        t[3]="|||||".getBytes(StandardCharsets.UTF_8);t[20]="..\\||".getBytes(StandardCharsets.UTF_8);
        t[27]="Near starving".getBytes(StandardCharsets.UTF_8);t[28]="Very thirsty".getBytes(StandardCharsets.UTF_8);
        t[29]="Dead Tired".getBytes(StandardCharsets.UTF_8);t[17]=":)".getBytes(StandardCharsets.UTF_8);
        return new Object[]{n,t};
    }
    static void common(Presentation p) throws Exception {
        HudTypeface font=(HudTypeface)field(p,"hudFont");
        check(p.window.background.color==Color.BLACK,"black window");
        check(p.content.background==Color.BLACK,"black scroll");
        check(((ViewGroup)p.content).children.get(0).background==Color.BLACK,"black content");
        check((p.window.flags&WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE)!=0,"window focus flag");
        check((p.window.flags&WindowManager.LayoutParams.FLAG_DIM_BEHIND)==0,"no dim");
        check(!p.content.focusable,"scroll focus");check(((ScrollView)p.content).fill,"fill viewport");
        check(((ViewGroup)p.content).descendants==ViewGroup.FOCUS_BLOCK_DESCENDANTS,"descendant focus");
        List<TextView> ts=texts(p.content);check(ts.size()==36,"36 text elements: "+ts.size());
        for(TextView t:ts){
            check(t.face==font.typeface,"shared font");check(t.color==Color.WHITE,"white text");
            check(!t.focusable,"text focus");check(t.spacing==0f,"letter spacing");
            check(t.features.equals("'liga' 0, 'clig' 0, 'kern' 0"),"shaping");
            check(Arrays.equals(t.padding,new int[]{0,8,0,8}),"text padding");
            float size=t==field(p,"value")?22f:t==field(p,"status")?12f:t==ts.get(0)?18f:16f;
            check(t.size==size,"unchanged size for "+t.text);
        }
        TextView[] widgets=(TextView[])field(p,"activityValues");
        for(int i=0;i<29;i++)check((widgets[i]==null)==(i>=5&&i<=13),"exact hidden slots "+i);
        for(LinearLayout row:pairs(p.content))check(!row.focusable&&row.descendants==ViewGroup.FOCUS_BLOCK_DESCENDANTS,"pair focus");
        ProgressBar stamina=(ProgressBar)field(p,"bar");
        check(stamina.params.width==ViewGroup.LayoutParams.MATCH_PARENT,"full-width stamina");
        check(stamina.maximum==1000,"stamina scale");
        long bars=descendants(p.content).stream().filter(v->v instanceof ProgressBar).count();
        check(bars==7,"seven bars, not extra meters");
    }
    static void mappingAndOrder(Presentation p,Object[] raw) throws Exception {
        ActivityHudSnapshot state=ActivityHudSnapshot.decode(raw);
        TextView[] w=(TextView[])field(p,"activityValues");TextView[] c=(TextView[])field(p,"coreValues");
        for(int i=0;i<w.length;i++)if(w[i]!=null)check(w[i].text.equals(state.label(i)),"widget mapping "+i);
        for(int i=0;i<c.length;i++)check(c[i].text.equals(state.core.coreLabel(i)),"core mapping "+i);
        ProgressBar[] hp=(ProgressBar[])field(p,"healthBars");
        LinearLayout body=(LinearLayout)field(p,"body");check(body.children.size()==3,"three health rows");
        int labelWidth=-1;
        for(int i=0;i<6;i++){
            LinearLayout pair=(LinearLayout)body.children.get(i/2);
            LinearLayout cell=(LinearLayout)pair.children.get(i%2);
            check(cell.children.size()==2,"label and bar same cell");
            TextView label=(TextView)cell.children.get(0);
            check(label.text.equals(PARTS[i]),"named left/right mapping");
            check(cell.children.get(1)==hp[i],"bar identity "+i);
            if(labelWidth<0)labelWidth=label.params.width;
            check(label.params.width==labelWidth,"aligned fixed label widths");
            check(labelWidth>=label.getPaint().measureText(label.text),"full health label fits modeled width");
            check(((LinearLayout.LayoutParams)hp[i].params).weight==1f,"flexible bar, no tiny label allocation");
            check(hp[i].maximum==1000&&hp[i].progress==(i+1)*100,"independent proportional hp "+i);
        }
        List<TextView> ordered=texts((View)field(p,"details"));
        List<TextView> expected=new ArrayList<>();
        for(int i=0;i<3;i++)expected.add(w[DISPLAY_ORDER[i]]);
        expected.add((TextView)field(p,"movement"));
        for(int i:CORE_ORDER)expected.add(c[i]);
        for(int i=3;i<DISPLAY_ORDER.length;i++)expected.add(w[DISPLAY_ORDER[i]]);
        check(ordered.equals(expected),"complete approved visual order");
        for(int i:new int[]{4,14,17,18,20,21,22,23,24,25,26,27}){
            check(w[i].parent==field(p,"details"),"full-width descriptive field "+i);
            check(w[i].params.width==ViewGroup.LayoutParams.MATCH_PARENT,"full width LP "+i);
        }
        check(((TextView)field(p,"movement")).params.width==ViewGroup.LayoutParams.MATCH_PARENT,"full movement label");
    }
    static void clearState(Presentation p,Object[] raw,String expected) throws Exception {
        call(p,"render",Object[].class,raw);
        check(((TextView)field(p,"value")).text.equals(expected),expected);
        check(((View)field(p,"body")).visibility==View.GONE,"body cleared");
        check(((View)field(p,"details")).visibility==View.GONE,"all mixed fields hidden");
        for(TextView t:(TextView[])field(p,"activityValues"))if(t!=null)check(t.text.isEmpty(),"widget cleared");
        for(TextView t:(TextView[])field(p,"coreValues"))check(t.text.isEmpty(),"core cleared");
        for(ProgressBar b:(ProgressBar[])field(p,"healthBars"))check(b.progress==0,"hp reset");
        check(((TextView)field(p,"movement")).text.isEmpty(),"movement cleared");
        check(((ProgressBar)field(p,"bar")).progress==0,"stamina reset");common(p);
    }
    public static void main(String[] args) throws Exception {
        String mode=args[0];Context context=new Context();
        if(mode.equals("fallback"))context.assets.failPrimary=true;
        if(mode.equals("large-font"))Paint.widthScale=2f;
        Class<?> c=Class.forName("com.cleverraven.cataclysmdda.DualScreenHud$HudPresentation");
        Constructor<?> ctor=c.getDeclaredConstructor(Context.class,Display.class);ctor.setAccessible(true);
        Presentation p=(Presentation)ctor.newInstance(context,new Display());
        call(p,"onCreate",Bundle.class,new Bundle());common(p);
        Object[] raw=snapshot();call(p,"render",Object[].class,raw);common(p);mappingAndOrder(p,raw);
        check(pairs(p.content).size()==10,"three health and seven metric pairs");
        for(LinearLayout row:pairs(p.content)){
            int minimum=(Integer)field(row,"pairWidth");
            measure(row,minimum,View.MeasureSpec.EXACTLY);check(row.getOrientation()==LinearLayout.HORIZONTAL,"boundary pair");
            LinearLayout.LayoutParams a=(LinearLayout.LayoutParams)row.children.get(0).params;
            LinearLayout.LayoutParams b=(LinearLayout.LayoutParams)row.children.get(1).params;
            check(a.width==0&&a.weight==1&&b.width==0&&b.weight==1&&a.rightMargin>0,"equal columns + gutter");
            int updates=row.children.get(0).setParamsCalls;
            measure(row,minimum,View.MeasureSpec.EXACTLY);check(row.children.get(0).setParamsCalls==updates,"no repeated layout mutation");
            measure(row,minimum-1,View.MeasureSpec.AT_MOST);check(row.getOrientation()==LinearLayout.VERTICAL,"narrow fallback");
            a=(LinearLayout.LayoutParams)row.children.get(0).params;
            check(a.width==ViewGroup.LayoutParams.MATCH_PARENT&&a.weight==0&&a.rightMargin==0,"full fallback rows");
            measure(row,0,View.MeasureSpec.UNSPECIFIED);check(row.getOrientation()==LinearLayout.HORIZONTAL,"unbounded measure");
            row.setPadding(10,0,10,0);measure(row,minimum+19,View.MeasureSpec.EXACTLY);
            check(row.getOrientation()==LinearLayout.VERTICAL,"padding accounted");row.setPadding(0,0,0,0);
            measure(row,minimum+100,View.MeasureSpec.EXACTLY);check(row.getOrientation()==LinearLayout.HORIZONTAL,"restore wide");
        }
        TextView[] w=(TextView[])field(p,"activityValues");
        if(mode.equals("blank")){
            for(int i:new int[]{26,27,28})((byte[][])raw[1])[i+1]=" \t ".getBytes(StandardCharsets.UTF_8);
        }else if(mode.equals("missing")){
            for(int i=0;i<29;i++)((long[])raw[0])[24+i]=0;
        }else if(mode.equals("long")){
            String longText="Very long description with unicode \\u2191 ";
            for(int i:new int[]{4,14,17,18,20,21,22,23,24,25,26,27})((byte[][])raw[1])[i+1]=(longText+longText+longText).getBytes(StandardCharsets.UTF_8);
        }else if(mode.equals("changing")){
            ((byte[][])raw[1])[29]="Exhausted".getBytes(StandardCharsets.UTF_8);
            ((byte[][])raw[1])[17]="D:".getBytes(StandardCharsets.UTF_8);
        }
        int[] orientations=pairs(p.content).stream().mapToInt(LinearLayout::getOrientation).toArray();
        call(p,"render",Object[].class,raw);mappingAndOrder(p,raw);common(p);
        check(Arrays.equals(orientations,pairs(p.content).stream().mapToInt(LinearLayout::getOrientation).toArray()),"no state-driven rearrangement");
        if(mode.equals("blank"))for(int i:new int[]{26,27,28})check(w[i].text.endsWith("\u2014"),"blank dash");
        if(mode.equals("missing"))for(TextView t:w)if(t!=null)check(t.text.endsWith("Unavailable"),"missing text preserved");
        if(mode.equals("long"))check(w[20].text.length()>100,"no truncation");
        if(mode.equals("fallback"))check(((HudTypeface)field(p,"hudFont")).typeface==Typeface.MONOSPACE,"font fallback retained");
        int fontCalls=context.assets.modernCalls+context.assets.legacyCalls;
        raw=snapshot();((long[])raw[0])[0]=0;clearState(p,raw,"No active game");
        raw=snapshot();((long[])raw[0])[1]=0;clearState(p,raw,"Waiting for the first game redraw");
        clearState(p,null,"Snapshot unavailable");
        clearState(p,new Object[]{new long[1],new byte[1][]},"Snapshot unavailable");
        raw=snapshot();call(p,"render",Object[].class,raw);mappingAndOrder(p,raw);common(p);
        check(((View)field(p,"details")).visibility==View.VISIBLE,"restore details");
        check(fontCalls==context.assets.modernCalls+context.assets.legacyCalls,"font not reloaded");
        check(((TextView)field(p,"status")).text.contains("Font: "),"footer preserved");
        System.out.println("layout host substitute passed: "+mode);
    }
}
