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

/** Production UI with host API substitutes; not an Android renderer or device test. */
public final class PolishHostTest {
    private static final String[] PARTS = {"Head", "Torso", "Left arm", "Right arm", "Left leg", "Right leg"};
    private static final int[] CORE_ORDER = {4, 5, 0, 1, 2, 3};
    private static final int[] AFTER_CORE = {27,26,28,16,0,1,2,3,17,18,19,14,20,21,22,23,24,25};

    static void check(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }
    static Object field(Object object, String name) throws Exception {
        Field f = object.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f.get(object);
    }
    static void call(Object object, String name, Class<?> type, Object value) throws Exception {
        Method m = object.getClass().getDeclaredMethod(name, type);
        m.setAccessible(true);
        m.invoke(object, value);
    }
    static List<View> descendants(View root) {
        List<View> result = new ArrayList<>();
        result.add(root);
        if (root instanceof ViewGroup) {
            for (View child : ((ViewGroup) root).children) result.addAll(descendants(child));
        }
        return result;
    }
    static List<TextView> texts(View root) {
        List<TextView> result = new ArrayList<>();
        for (View v : descendants(root)) if (v instanceof TextView) result.add((TextView) v);
        return result;
    }
    static List<LinearLayout> pairs(View root) {
        List<LinearLayout> result = new ArrayList<>();
        for (View v : descendants(root)) {
            if (v.getClass().getSimpleName().equals("StablePairRow")) result.add((LinearLayout) v);
        }
        return result;
    }
    static void measure(View row, int width, int mode) {
        row.measure(View.MeasureSpec.makeMeasureSpec(width, mode),
                    View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
    }
    static Object[] snapshot() {
        long[] n = new long[53];
        n[0]=1; n[1]=1; n[2]=640; n[3]=1000; n[4]=15; n[5]=125;
        for (int i=0; i<6; i++) { n[6+2*i]=10*(i+1); n[7+2*i]=100; n[18+i]=11+i; }
        byte[][] t = new byte[30][];
        t[0] = "walk (W)".getBytes(StandardCharsets.UTF_8);
        for (int i=0; i<29; i++) { n[24+i]=1; t[i+1]=("field "+i).getBytes(StandardCharsets.UTF_8); }
        t[16]="0".getBytes(StandardCharsets.UTF_8);
        t[20]="..\\||".getBytes(StandardCharsets.UTF_8);
        t[27]="Near starving".getBytes(StandardCharsets.UTF_8);
        t[28]="Very thirsty".getBytes(StandardCharsets.UTF_8);
        t[29]="Dead Tired".getBytes(StandardCharsets.UTF_8);
        return new Object[]{n,t};
    }
    static void common(Presentation p) throws Exception {
        HudTypeface font = (HudTypeface) field(p,"hudFont");
        check(p.window.background.color==Color.BLACK,"black window");
        check(p.content.background==Color.BLACK,"black scrolling viewport");
        check(((ViewGroup)p.content).children.get(0).background==Color.BLACK,"black content");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE)!=0,"nonfocusable window");
        check((p.window.flags & WindowManager.LayoutParams.FLAG_DIM_BEHIND)==0,"no dimming");
        check(!p.content.focusable && ((ScrollView)p.content).fill,"scroll flags");
        check(((ViewGroup)p.content).descendants==ViewGroup.FOCUS_BLOCK_DESCENDANTS,"descendant focus");
        List<TextView> all = texts(p.content);
        check(all.size()==36,"all 36 text elements retained");
        check(all.get(0).text.equals("CDDA-DS / HUD POLISH"),"diagnostic title");
        for (TextView t : all) {
            check(t.face==font.typeface && t.color==Color.WHITE,"shared font and color");
            check(!t.focusable && t.spacing==0f,"text flags and spacing");
            check(t.features.equals("'liga' 0, 'clig' 0, 'kern' 0"),"shaping unchanged");
            check(Arrays.equals(t.padding,new int[]{0,8,0,8}),"text padding unchanged");
            float size = t==field(p,"value") ? 22f : t==field(p,"status") ? 12f : t==all.get(0) ? 18f : 16f;
            check(t.size==size,"font sizes unchanged");
            check(t.gravityCalls==0,"original default text alignment restored without gravity override");
        }
        TextView[] w = (TextView[]) field(p,"activityValues");
        for (int i=0; i<29; i++) check((w[i]==null)==(i>=5 && i<=13),"exact hidden fields "+i);
        ProgressBar stamina = (ProgressBar) field(p,"bar");
        check(stamina.params.width==ViewGroup.LayoutParams.MATCH_PARENT,"stamina full width");
        check(stamina.maximum==1000,"stamina scale");
        check(descendants(p.content).stream().filter(v -> v instanceof ProgressBar).count()==7,"seven bars");
        check(pairs(p.content).size()==11,"three health pairs and eight metric pairs");
    }
    static void orderAndMapping(Presentation p, Object[] raw) throws Exception {
        ActivityHudSnapshot state = ActivityHudSnapshot.decode(raw);
        TextView[] w = (TextView[]) field(p,"activityValues");
        TextView[] c = (TextView[]) field(p,"coreValues");
        TextView move = (TextView) field(p,"movement");
        for (int i=0; i<w.length; i++) if (w[i]!=null) check(w[i].text.equals(state.label(i)),"widget "+i);
        for (int i=0; i<c.length; i++) check(c[i].text.equals(state.core.coreLabel(i)),"core "+i);
        check(move.text.equals("Movement mode: "+state.core.movementMode),"movement value unchanged");
        List<TextView> expected = new ArrayList<>();
        expected.add(w[4]); expected.add(move); expected.add(w[15]);
        for (int i : CORE_ORDER) expected.add(c[i]);
        for (int i : AFTER_CORE) expected.add(w[i]);
        check(texts((View)field(p,"details")).equals(expected),"complete reading order and no duplicates");
        for (int i : new int[]{4,14,17,18,19,20,21,22,23,24,25}) {
            check(w[i].parent==field(p,"details"),"full-width descriptive row "+i);
            check(w[i].params.width==ViewGroup.LayoutParams.MATCH_PARENT,"full width params "+i);
        }
        check(move.parent==w[15].parent,"movement and Sound share one row");
        LinearLayout mp = (LinearLayout) move.parent;
        check(mp.children.get(0)==move && mp.children.get(1)==w[15],"Movement left, Sound right");
        check(w[27].parent==w[26].parent,"retained needs pairing");
        LinearLayout np = (LinearLayout) w[27].parent;
        check(np.children.get(0)==w[27] && np.children.get(1)==w[26],"Thirst left, Hunger right");
        ProgressBar[] hp = (ProgressBar[]) field(p,"healthBars");
        LinearLayout body = (LinearLayout) field(p,"body");
        check(body.children.size()==3,"three health rows");
        int labelWidth = -1;
        for (int i=0; i<6; i++) {
            LinearLayout row=(LinearLayout)body.children.get(i/2);
            LinearLayout cell=(LinearLayout)row.children.get(i%2);
            check(cell.children.size()==2,"label/bar cells");
            TextView label=(TextView)cell.children.get(0);
            check(label.text.equals(PARTS[i]),"full names, no added whitespace, no mirroring");
            if (labelWidth<0) labelWidth=label.params.width;
            check(label.params.width==labelWidth,"fixed equal label boxes");
            check(labelWidth>=label.getPaint().measureText(label.text),"labels fit modeled box");
            check(cell.children.get(1)==hp[i],"correct bar for part");
            LinearLayout.LayoutParams track=(LinearLayout.LayoutParams)hp[i].params;
            check(track.leftMargin==4 && track.width==0 && track.weight==1f,"bar geometry unchanged");
            check(hp[i].maximum==1000 && hp[i].progress==(i+1)*100,"independent proportional health");
        }
    }
    static void widthChecks(Presentation p, String[] args) throws Exception {
        for (LinearLayout row : pairs(p.content)) {
            check(!row.focusable && row.descendants==ViewGroup.FOCUS_BLOCK_DESCENDANTS,"pair focus");
            int minimum = (Integer) field(row,"pairWidth");
            measure(row,minimum,View.MeasureSpec.EXACTLY);
            check(row.getOrientation()==LinearLayout.HORIZONTAL,"pair at boundary");
            LinearLayout.LayoutParams a=(LinearLayout.LayoutParams)row.children.get(0).params;
            LinearLayout.LayoutParams b=(LinearLayout.LayoutParams)row.children.get(1).params;
            check(a.width==0 && a.weight==1f && b.width==0 && b.weight==1f && a.rightMargin>0,"equal columns");
            int calls=row.children.get(0).setParamsCalls;
            measure(row,minimum,View.MeasureSpec.EXACTLY);
            check(row.children.get(0).setParamsCalls==calls,"no repeated layout mutation");
            measure(row,minimum-1,View.MeasureSpec.AT_MOST);
            check(row.getOrientation()==LinearLayout.VERTICAL,"narrow fallback");
            a=(LinearLayout.LayoutParams)row.children.get(0).params;
            check(a.width==ViewGroup.LayoutParams.MATCH_PARENT && a.weight==0 && a.rightMargin==0,"stacked geometry");
            row.setPadding(10,0,10,0); measure(row,minimum+19,View.MeasureSpec.EXACTLY);
            check(row.getOrientation()==LinearLayout.VERTICAL,"padding counted");
            row.setPadding(0,0,0,0); measure(row,0,View.MeasureSpec.UNSPECIFIED);
            check(row.getOrientation()==LinearLayout.HORIZONTAL,"unbounded fallback");
            measure(row,minimum,View.MeasureSpec.EXACTLY);
        }
        TextView move=(TextView)field(p,"movement");
        LinearLayout row=(LinearLayout)move.parent;
        int width=(Integer)field(row,"pairWidth"), gap=(Integer)field(row,"gap");
        int expected=2*((int)Math.ceil(move.getPaint().measureText("Movement mode: crouch (C)"))+2)+gap;
        check(width==expected,"fixed movement width probe");
        for (int i=1; i<args.length; i++) {
            Object[] raw=snapshot(); ((byte[][])raw[1])[0]=args[i].getBytes(StandardCharsets.UTF_8);
            int calls=move.setParamsCalls; call(p,"render",Object[].class,raw);
            check(move.getPaint().measureText(move.text)+2<=(width-gap)/2,"all pinned modes and Unknown fit modeled budget");
            check(move.setParamsCalls==calls && row.getOrientation()==LinearLayout.HORIZONTAL,"mode change not layout trigger");
        }
        call(p,"render",Object[].class,snapshot());
    }
    static void staminaChecks(Presentation p) throws Exception {
        long[][] inputs={{0,8500},{4250,8500},{8500,8500},{8499,8500},{1,3},{9000,8500}};
        String[] expected={"0.0%","50.0%","100.0%","100.0%","33.3%","105.9%"};
        int[] progress={0,500,1000,999,333,1000};
        for (int i=0; i<inputs.length; i++) {
            Object[] raw=snapshot(); long[] n=(long[])raw[0]; n[2]=inputs[i][0]; n[3]=inputs[i][1];
            call(p,"render",Object[].class,raw);
            check(((TextView)field(p,"value")).text.equals("Stamina: "+expected[i]),"percentage only, precision unchanged");
            check(((ProgressBar)field(p,"bar")).progress==progress[i],"bar math unchanged");
            ActivityHudSnapshot decoded=ActivityHudSnapshot.decode(raw);
            check(decoded.core.current==inputs[i][0] && decoded.core.maximum==inputs[i][1],"raw values preserved internally");
        }
    }
    static void cleared(Presentation p, Object[] raw, String expected) throws Exception {
        call(p,"render",Object[].class,raw);
        check(((TextView)field(p,"value")).text.equals(expected),"status message "+expected);
        check(((View)field(p,"body")).visibility==View.GONE,"hidden health");
        check(((View)field(p,"details")).visibility==View.GONE,"hidden readings");
        for (TextView w : (TextView[])field(p,"activityValues")) if (w!=null) check(w.text.isEmpty(),"clear widgets");
        for (TextView c : (TextView[])field(p,"coreValues")) check(c.text.isEmpty(),"clear core");
        check(((TextView)field(p,"movement")).text.isEmpty(),"clear movement");
        for (ProgressBar hp : (ProgressBar[])field(p,"healthBars")) check(hp.progress==0,"clear health");
        check(((ProgressBar)field(p,"bar")).progress==0,"clear stamina");
        common(p);
    }
    public static void main(String[] args) throws Exception {
        String mode=args[0]; Context context=new Context();
        if (mode.equals("fallback")) context.assets.failPrimary=true;
        if (mode.equals("large-font")) Paint.widthScale=2f;
        Class<?> cls=Class.forName("com.cleverraven.cataclysmdda.DualScreenHud$HudPresentation");
        Constructor<?> ctor=cls.getDeclaredConstructor(Context.class,Display.class); ctor.setAccessible(true);
        Presentation p=(Presentation)ctor.newInstance(context,new Display());
        call(p,"onCreate",Bundle.class,new Bundle()); common(p);
        Object[] raw=snapshot(); call(p,"render",Object[].class,raw); orderAndMapping(p,raw); widthChecks(p,args);
        if (mode.equals("blank")) {
            for (int i : new int[]{19,26,27,28}) ((byte[][])raw[1])[i+1]=" \t ".getBytes(StandardCharsets.UTF_8);
        } else if (mode.equals("missing")) {
            for (int i=0; i<29; i++) ((long[])raw[0])[24+i]=0;
        } else if (mode.equals("long")) {
            String text="A deliberately long descriptive value with unicode \u2191 ";
            for (int i=0; i<30; i++) ((byte[][])raw[1])[i]=(text+text+text).getBytes(StandardCharsets.UTF_8);
        } else if (mode.equals("changing")) {
            ((byte[][])raw[1])[0]="crouch (C)".getBytes(StandardCharsets.UTF_8);
            ((byte[][])raw[1])[16]="12345".getBytes(StandardCharsets.UTF_8);
            ((byte[][])raw[1])[20]="|||||".getBytes(StandardCharsets.UTF_8);
        }
        int[] orientations=pairs(p.content).stream().mapToInt(LinearLayout::getOrientation).toArray();
        call(p,"render",Object[].class,raw); orderAndMapping(p,raw); common(p);
        check(Arrays.equals(orientations,pairs(p.content).stream().mapToInt(LinearLayout::getOrientation).toArray()),"values never rearrange columns");
        TextView[] w=(TextView[])field(p,"activityValues");
        if (mode.equals("blank")) for(int i:new int[]{19,26,27,28}) check(w[i].text.endsWith("\u2014"),"blank dash");
        if (mode.equals("missing")) for(TextView t:w) if(t!=null) check(t.text.endsWith("Unavailable"),"missing state");
        if (mode.equals("long")) check(w[19].text.length()>100 && ((TextView)field(p,"movement")).text.length()>100,"no truncation");
        if (mode.equals("fallback")) check(((HudTypeface)field(p,"hudFont")).typeface==Typeface.MONOSPACE,"font fallback");
        if (mode.equals("stamina")) staminaChecks(p);
        int fontCalls=context.assets.modernCalls+context.assets.legacyCalls;
        raw=snapshot(); ((long[])raw[0])[0]=0; cleared(p,raw,"No active game");
        raw=snapshot(); ((long[])raw[0])[1]=0; cleared(p,raw,"Waiting for the first game redraw");
        raw=snapshot(); ((long[])raw[0])[3]=0; cleared(p,raw,"Waiting for the first game redraw");
        cleared(p,null,"Snapshot unavailable");
        cleared(p,new Object[]{new long[1],new byte[1][]},"Snapshot unavailable");
        raw=snapshot(); call(p,"render",Object[].class,raw); orderAndMapping(p,raw); common(p);
        check(((View)field(p,"details")).visibility==View.VISIBLE,"reload restores readings");
        check(fontCalls==context.assets.modernCalls+context.assets.legacyCalls,"font not reloaded");
        check(((TextView)field(p,"status")).text.contains("Font: "),"footer preserved");
        System.out.println("polish host substitute passed: "+mode);
    }
}
