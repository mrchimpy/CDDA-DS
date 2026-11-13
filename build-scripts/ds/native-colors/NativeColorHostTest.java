package com.cleverraven.cataclysmdda;

import android.app.Presentation;
import android.content.Context;
import android.graphics.Paint;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.style.BackgroundColorSpan;
import android.text.style.ForegroundColorSpan;
import android.view.Display;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Executes production UI/decoder code and the real JNI transport, with API/game substitutes. */
public final class NativeColorHostTest {
    private static native void seed(int mode);
    private static final int GRAY=0xff969696, RED=0xffff0000, GREEN=0xff006e00, BLACK=0xff000000;
    private static void check(boolean result,String message){if(!result)throw new AssertionError(message);}
    private static Object field(Object object,String name)throws Exception {
        Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(object);
    }
    private static Object call(Object object,String name,Class<?> type,Object arg)throws Exception {
        Method m=object.getClass().getDeclaredMethod(name,type);m.setAccessible(true);return m.invoke(object,arg);
    }
    private static Object[] snapshot(int mode)throws Exception {
        seed(mode);Method m=DualScreenHud.class.getDeclaredMethod("nativeSnapshot");m.setAccessible(true);
        return (Object[])m.invoke(null);
    }
    private static Presentation panel(boolean fallback)throws Exception {
        Context context=new Context();context.assets.failPrimary=fallback;
        Class<?> c=Class.forName("com.cleverraven.cataclysmdda.DualScreenHud$HudPresentation");
        Constructor<?> ctor=c.getDeclaredConstructor(Context.class,Display.class);ctor.setAccessible(true);
        Presentation p=(Presentation)ctor.newInstance(context,new Display());
        call(p,"onCreate",Bundle.class,null);return p;
    }
    private static void render(Presentation panel,Object[] raw)throws Exception {call(panel,"render",Object[].class,raw);}
    private static TextView text(Presentation p,String name)throws Exception{return (TextView)field(p,name);}
    private static String content(TextView t){return t.text.toString();}
    private static TextView[] widgets(Presentation p)throws Exception{return (TextView[])field(p,"activityValues");}
    private static TextView[] core(Presentation p)throws Exception{return (TextView[])field(p,"coreValues");}
    private static ProgressBar[] bars(Presentation p)throws Exception{return (ProgressBar[])field(p,"healthBars");}
    private static int ink(TextView view,int index,boolean background){
        int result=background?BLACK:view.color;
        if(view.text instanceof SpannableString){
            for(SpannableString.Entry entry:((SpannableString)view.text).spans){
                if(entry.start<=index&&index<entry.end){
                    if(background&&entry.span instanceof BackgroundColorSpan)result=((BackgroundColorSpan)entry.span).color;
                    if(!background&&entry.span instanceof ForegroundColorSpan)result=((ForegroundColorSpan)entry.span).color;
                }
            }
        }
        return result;
    }
    private static int valueInk(TextView view){return ink(view,content(view).indexOf(": ")+2,false);}
    private static List<TextView> texts(View root){
        List<TextView> result=new ArrayList<>();
        if(root instanceof TextView)result.add((TextView)root);
        if(root instanceof ViewGroup)for(View child:((ViewGroup)root).children)result.addAll(texts(child));
        return result;
    }
    private static int countPairs(View root){
        int result=root.getClass().getSimpleName().equals("StablePairRow")?1:0;
        if(root instanceof ViewGroup)for(View child:((ViewGroup)root).children)result+=countPairs(child);
        return result;
    }
    private static void base(Presentation p)throws Exception{
        render(p,snapshot(1));
        check(content(text(p,"value")).equals("Stamina: 50.0%"),"percentage only");
        ProgressBar stamina=(ProgressBar)field(p,"bar");
        check(stamina.progress==500&&stamina.maximum==1000,"unchanged stamina scale");
        check(stamina.tint.getDefaultColor()==0xffffff00,"native stamina color");
        check(valueInk(text(p,"value"))==0xffffff00,"percentage uses bar color");
        check(ink(text(p,"value"),0,false)==GRAY,"neutral stamina label");
        TextView[] labels=(TextView[])field(p,"bodyLabels");
        check(ink(labels[0],0,false)==0xff8b3a62&&ink(labels[0],0,true)==RED,"independent limb label highlight");
        check(bars(p)[0].tint.getDefaultColor()==RED,"low HP native color");
        for(int i=0;i<6;i++)check(bars(p)[i].progress==(i+1)*100,"HP mapping preserved");
        check(valueInk(core(p)[0])==0xffffffff,"base stat white");
        check(valueInk(core(p)[1])==0xffff9696,"stat penalty light red");
        check(valueInk(core(p)[2])==RED,"larger penalty red");
        check(valueInk(core(p)[3])==0xff00ff00,"stat bonus light green");
        check(valueInk(text(p,"movement"))==RED,"native movement color");
        TextView[] w=widgets(p);
        for(int i=0;i<29;i++)check((w[i]==null)==(i>=5&&i<=13),"nine rows stay absent");
        check(w[17].parent==w[18].parent,"one comfort pair");
        check(w[17].parent.children.get(0)==w[17],"comfort left");
        check(w[18].parent.children.get(1)==w[18],"trend right");
        check(valueInk(w[17])==GREEN&&valueInk(w[18])==0xff3333ff,"native comfort/trend colors");
        check(countPairs(p.content)==12,"only one new pair");
        check(texts(p.content).size()==36,"no extra text views");
        List<TextView> order=texts(p.content);
        int last=-1;
        for(int i:new int[]{4,15,27,26,28,16,0,1,2,3,17,18,19,14,20,21,22,23,24,25}){
            int at=order.indexOf(w[i]);check(at>last,"widget order "+i);last=at;
        }
        check(w[19].parent==field(p,"details")&&w[20].parent==field(p,"details"),"oxygen and clothing full width");
        check(content(text(p,"status")).contains("Font: Terminus + Unifont"),"font unchanged");
        check(!content(text(p,"status")).contains("unavailable"),"valid native colors");
        check((p.window.flags&8)!=0&&(p.window.flags&2)==0,"window focus/dimming flags preserved");
        for(TextView t:order)check(!t.focusable,"no interactive controls");
    }
    private static int countOffset(long[] words,int field){
        int pos=50;
        for(int i=0;i<field;i++)pos+=1+4*(int)words[pos];
        return pos;
    }
    private static void fallback(Presentation p,Object[] raw)throws Exception{
        render(p,raw);
        check(content(text(p,"value")).equals("Stamina: 50.0%"),"malformed color does not erase values");
        check(valueInk(text(p,"value"))==GRAY,"neutral fallback replaces old color");
        check(content(text(p,"status")).contains("Native colors unavailable"),"fallback is visible");
    }
    public static void main(String[] args)throws Exception{
        System.load(args[0]);String mode=args[1];
        if(mode.equals("large-font"))Paint.widthScale=1.75f;
        Presentation p=panel(mode.equals("font-fallback"));
        if(!mode.equals("font-fallback"))base(p);
        if(mode.equals("normal")){} // base covers the complete UI map.
        else if(mode.equals("unicode")){
            TextView t=widgets(p)[20];String s=content(t);
            check(s.endsWith("\ud83d\ude00"),"supplementary character retained");
            check(ink(t,s.length()-1,false)==RED&&ink(t,s.length()-2,false)==RED,"UTF16 surrogate pair color");
            check(valueInk(t)==GREEN,"first clothing segment green");
            check(ink(t,s.indexOf("Jacket"),false)==GRAY,"middle clothing segment gray");
            for(SpannableString.Entry e:((SpannableString)t.text).spans)check(e.end<=s.length(),"span bounds");
        } else if(mode.equals("malformed")){
            for(int at:new int[]{0,1,2,3,4,5,8,49}){
                Object[] raw=snapshot(1);((long[])raw[2])[at]=-1;fallback(p,raw);
            }
            Object[] raw=snapshot(1);raw[2]=new long[0];fallback(p,raw);
            raw=snapshot(1);raw[2]=null;fallback(p,raw);
            raw=snapshot(1);raw[2]=Arrays.copyOf((long[])raw[2],((long[])raw[2]).length+1);fallback(p,raw);
            raw=snapshot(1);long[] words=(long[])raw[2];int at=countOffset(words,20);
            // Third run ends inside the four-byte emoji, not at a UTF-8 boundary.
            words[at+1+2*4+1]--;fallback(p,raw);
        } else if(mode.equals("blank")){
            render(p,snapshot(4));
            for(TextView t:widgets(p))if(t!=null){check(content(t).endsWith("\u2014"),"blank dash");check(valueInk(t)==GRAY,"blank clears color");}
        } else if(mode.equals("missing")){
            Object[] raw=snapshot(4);((long[])raw[0])[24+26]=0;render(p,raw);
            check(content(widgets(p)[26]).equals("Hunger: Unavailable"),"missing not blank");
            check(valueInk(widgets(p)[26])==GRAY,"missing clears color");
        } else if(mode.equals("lifecycle")){
            for(int state:new int[]{0,3}){
                render(p,snapshot(state));
                check(((View)field(p,"body")).visibility==View.GONE,"body hidden");
                check(((View)field(p,"details")).visibility==View.GONE,"details hidden");
                check(!(text(p,"value").text instanceof SpannableString),"no stale percentage spans");
                TextView[] labels=(TextView[])field(p,"bodyLabels");
                check(!(labels[0].text instanceof SpannableString),"condition background cleared");
                for(TextView t:widgets(p))if(t!=null)check(content(t).isEmpty(),"readings cleared");
                check(bars(p)[0].progress==0,"bar cleared");base(p);
            }
        } else if(mode.equals("zero")){
            render(p,snapshot(2));
            check(content(text(p,"value")).equals("Stamina: 0.0%"),"zero percentage");
            ProgressBar b=(ProgressBar)field(p,"bar");
            check(b.progress==0&&b.track.getDefaultColor()==RED,"empty stamina track warning; no fake fill");
            check(bars(p)[0].progress==0&&bars(p)[0].track.getDefaultColor()==RED,"empty HP track warning");
            base(p);check(((ProgressBar)field(p,"bar")).track.getDefaultColor()==0xff636363,"track restored");
        } else if(mode.equals("recovery")){
            render(p,snapshot(6));
            for(int i=0;i<6;i++)check(valueInk(core(p)[i])==0xffffffff,"stat recovery resets native white");
            check(valueInk(text(p,"movement"))==0xffffffff,"walk clears running color");
            TextView head=((TextView[])field(p,"bodyLabels"))[0];
            check(ink(head,0,false)==GRAY&&ink(head,0,true)==BLACK,"recovery clears limb highlight without menu");
            check(valueInk(text(p,"value"))==GREEN,"recovered stamina native green");
        } else if(mode.equals("rounding")){
            render(p,snapshot(7));
            check(content(text(p,"value")).equals("Stamina: 12.5%"),"rounding retained");
            check(valueInk(text(p,"value"))==RED,"color follows 12.49%, not rounded 12.5%");
        } else if(mode.equals("palette")){
            render(p,snapshot(5));
            check(ink(text(p,"value"),0,false)==0xff123456,"copied native neutral foreground");
            check(ink(text(p,"value"),0,true)==0xff010203,"copied neutral background");
            check(valueInk(text(p,"value"))==0xffabcdef,"copied native scalar RGB");
            base(p);
        } else if(mode.equals("copy")){
            Object[] raw=snapshot(1);ActivityHudSnapshot a=ActivityHudSnapshot.decode(NativeHudColors.values(raw));
            NativeHudColors c=NativeHudColors.decode(raw,a);
            Arrays.fill((long[])raw[2],0);((byte[][])raw[1])[21][0]='x';
            TextView v=new TextView(new Context());c.widget(v,a,20);
            check(content(v).startsWith("Worn head: ++ ")&&valueInk(v)==GREEN,"immutable decoded strings and styles");
            c.scalar(v,"Stamina: 50.0%",9,0);check(valueInk(v)==0xffffff00,"immutable scalar copy");
        } else if(mode.equals("width")||mode.equals("large-font")){
            TextView[] w=widgets(p);LinearLayout row=(LinearLayout)w[17].parent;
            int minimum=(Integer)field(row,"pairWidth");
            int height=View.MeasureSpec.makeMeasureSpec(0,View.MeasureSpec.UNSPECIFIED);
            row.measure(View.MeasureSpec.makeMeasureSpec(minimum,View.MeasureSpec.EXACTLY),height);
            check(row.getOrientation()==LinearLayout.HORIZONTAL,"comfort pair at boundary");
            int before=w[17].setParamsCalls;
            render(p,snapshot(4));check(w[17].setParamsCalls==before,"values do not rearrange");
            row.measure(View.MeasureSpec.makeMeasureSpec(minimum-1,View.MeasureSpec.EXACTLY),height);
            check(row.getOrientation()==LinearLayout.VERTICAL,"narrow comfort fallback");
            row.measure(View.MeasureSpec.makeMeasureSpec(minimum,View.MeasureSpec.EXACTLY),height);
            check(row.getOrientation()==LinearLayout.HORIZONTAL,"width recovery");
        } else if(mode.equals("partial")){
            Object[] raw=snapshot(1);((long[])raw[2])[4]=0;render(p,raw);
            check(content(text(p,"status")).contains("Some native colors unavailable"),"partial warning");
            check(valueInk(text(p,"value"))==0xffffff00,"known colors retained");
        } else if(mode.equals("font-fallback")){
            render(p,snapshot(1));check(content(text(p,"status")).contains("Android monospace"),"font fallback retained");
            check(valueInk(text(p,"value"))==0xffffff00,"colors independent of typeface");
        } else throw new AssertionError("Unknown scenario "+mode);
        System.out.println("native color host passed: "+mode);
    }
}
