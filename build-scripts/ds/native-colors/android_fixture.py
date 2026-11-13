"""Host-only Android API substitutes. Not a renderer, font engine or device test."""
from pathlib import Path

SOURCES = {
'android.annotation.TargetApi': 'public @interface TargetApi { int value(); }',
'android.R': '''public final class R {
 public static final class style { public static final int Theme_Material_NoActionBar=1; }
 public static final class attr { public static final int progressBarStyleHorizontal=2; }
}''',
'android.content.res.AssetManager': 'public class AssetManager { public boolean failPrimary, failFallback, failModern; }',
'android.content.res.Resources': '''public class Resources {
 public android.util.DisplayMetrics getDisplayMetrics(){return new android.util.DisplayMetrics();}
}''',
'android.content.res.ColorStateList': '''public class ColorStateList {
 private final int color; private ColorStateList(int c){color=c;}
 public static ColorStateList valueOf(int c){return new ColorStateList(c);}
 public int getDefaultColor(){return color;}
}''',
'android.content.Context': '''public class Context {
 public static final String DISPLAY_SERVICE="display";
 public final android.content.res.AssetManager assets=new android.content.res.AssetManager();
 public android.content.res.AssetManager getAssets(){return assets;}
 public android.content.res.Resources getResources(){return new android.content.res.Resources();}
 public Object getSystemService(String s){return new android.hardware.display.DisplayManager();}
}''',
'android.content.DialogInterface': '''public interface DialogInterface {
 interface OnDismissListener { void onDismiss(DialogInterface d); }
}''',
'android.util.DisplayMetrics': 'public class DisplayMetrics { public float density=1; }',
'android.util.Log': '''public class Log {
 public static int i(String a,String b){return 0;}
 public static int w(String a,String b,Throwable c){return 0;}
 public static int e(String a,String b,Throwable c){return 0;}
}''',
'android.graphics.Color': 'public class Color { public static final int WHITE=0xffffffff,BLACK=0xff000000; }',
'android.graphics.PorterDuff': 'public class PorterDuff { public enum Mode { SRC_IN } }',
'android.graphics.Paint': '''public class Paint {
 public static float widthScale=1; public float size=16;
 public float measureText(String s){return s.codePointCount(0,s.length())*size*0.5f*widthScale;}
}''',
'android.graphics.drawable.ColorDrawable': 'public class ColorDrawable { public final int color; public ColorDrawable(int c){color=c;} }',
'android.graphics.fonts.FontStyle': 'public class FontStyle {}',
'android.graphics.fonts.Font': '''public class Font {
 public final String path; Font(String p){path=p;}
 public FontStyle getStyle(){return new FontStyle();}
 public static class Builder {
  final android.content.res.AssetManager assets; final String path;
  public Builder(android.content.res.AssetManager a,String p){assets=a;path=p;}
  public Font build() throws java.io.IOException {
   if(assets.failModern || (path.contains("Terminus")?assets.failPrimary:assets.failFallback))
    throw new java.io.IOException("fixture font failure");
   return new Font(path);
  }
 }
}''',
'android.graphics.fonts.FontFamily': '''public class FontFamily {
 public final Font font; FontFamily(Font f){font=f;}
 public static class Builder { final Font font;
  public Builder(Font f){font=f;} public FontFamily build(){return new FontFamily(font);}
 }
}''',
'android.graphics.Typeface': '''public class Typeface {
 public final String path; public String fallback="";
 Typeface(String p){path=p;} public static final Typeface MONOSPACE=new Typeface("monospace");
 public static Typeface createFromAsset(android.content.res.AssetManager a,String p){
  if(a.failPrimary)throw new IllegalArgumentException("fixture font failure");return new Typeface(p);
 }
 public static class CustomFallbackBuilder {
  final Typeface result;
  public CustomFallbackBuilder(android.graphics.fonts.FontFamily f){result=new Typeface(f.font.path);}
  public CustomFallbackBuilder addCustomFallback(android.graphics.fonts.FontFamily f){result.fallback=f.font.path;return this;}
  public CustomFallbackBuilder setStyle(android.graphics.fonts.FontStyle s){return this;}
  public CustomFallbackBuilder setSystemFallback(String s){return this;}
  public Typeface build(){return result;}
 }
}''',
'android.os.Build': 'public class Build { public static class VERSION { public static int SDK_INT=35; } }',
'android.os.Bundle': 'public class Bundle {}',
'android.os.Looper': 'public class Looper { public static Looper getMainLooper(){return new Looper();} }',
'android.os.Handler': '''public class Handler {
 public Handler(Looper l){} public void post(Runnable r){} public void postDelayed(Runnable r,long d){}
 public void removeCallbacks(Runnable r){}
}''',
'android.view.Display': '''public class Display {
 public static final int STATE_OFF=1;
 public int getDisplayId(){return 1;} public String getName(){return "host fixture";}
 public int getFlags(){return 0;} public int getState(){return 2;} public boolean isValid(){return true;}
}''',
'android.view.MotionEvent': 'public class MotionEvent {}',
'android.view.Gravity': 'public class Gravity { public static final int CENTER_VERTICAL=16; }',
'android.view.View': '''public class View {
 public static final int VISIBLE=0,GONE=8;
 public int background=0x11223344,visibility=VISIBLE,setParamsCalls; public boolean focusable;
 public int[] padding=new int[4]; public final android.content.Context context;
 public ViewGroup.LayoutParams params; public ViewGroup parent;
 public View(android.content.Context c){context=c;}
 public void setBackgroundColor(int c){background=c;} public void setFocusable(boolean b){focusable=b;}
 public void setVisibility(int v){visibility=v;} public void setPadding(int a,int b,int c,int d){padding=new int[]{a,b,c,d};}
 public void setOnTouchListener(OnTouchListener l){} public Display getDisplay(){return new Display();}
 public int getPaddingLeft(){return padding[0];} public int getPaddingRight(){return padding[2];}
 public void setLayoutParams(ViewGroup.LayoutParams p){params=p;setParamsCalls++;}
 public ViewGroup.LayoutParams getLayoutParams(){return params;}
 protected void onMeasure(int w,int h){} public final void measure(int w,int h){onMeasure(w,h);}
 public interface OnTouchListener { boolean onTouch(View v,MotionEvent e); }
 public static final class MeasureSpec {
  public static final int UNSPECIFIED=0,EXACTLY=0x40000000,AT_MOST=0x80000000;
  public static int getSize(int s){return s&0x3fffffff;} public static int getMode(int s){return s&0xc0000000;}
  public static int makeMeasureSpec(int s,int m){return (s&0x3fffffff)|m;}
 }
}''',
'android.view.ViewGroup': '''public class ViewGroup extends View {
 public static final int FOCUS_BLOCK_DESCENDANTS=0x60000; public int descendants;
 public final java.util.List<View> children=new java.util.ArrayList<>();
 public ViewGroup(android.content.Context c){super(c);}
 public void addView(View v){if(v.parent!=null)throw new IllegalStateException();v.parent=this;children.add(v);}
 public void addView(View v,LayoutParams p){v.setLayoutParams(p);addView(v);}
 public void setDescendantFocusability(int v){descendants=v;}
 public static class LayoutParams {
  public static final int MATCH_PARENT=-1,WRAP_CONTENT=-2; public int width,height;
  public LayoutParams(int w,int h){width=w;height=h;}
 }
}''',
'android.view.Window': '''public class Window {
 public int flags,width,height; public android.graphics.drawable.ColorDrawable background;
 public void addFlags(int f){flags|=f;} public void clearFlags(int f){flags&=~f;}
 public void setBackgroundDrawable(android.graphics.drawable.ColorDrawable d){background=d;}
 public void setLayout(int w,int h){width=w;height=h;}
 public View getDecorView(){return new View(new android.content.Context());}
}''',
'android.view.WindowManager': '''public class WindowManager {
 public Display getDefaultDisplay(){return new Display();}
 public static class LayoutParams extends ViewGroup.LayoutParams {
  public static final int FLAG_NOT_FOCUSABLE=8,FLAG_DIM_BEHIND=2;
  public LayoutParams(int w,int h){super(w,h);}
 }
}''',
'android.hardware.display.DisplayManager': '''public class DisplayManager {
 public static final String DISPLAY_CATEGORY_PRESENTATION="presentation";
 public void registerDisplayListener(DisplayListener l,android.os.Handler h){}
 public void unregisterDisplayListener(DisplayListener l){}
 public android.view.Display[] getDisplays(){return new android.view.Display[]{new android.view.Display()};}
 public android.view.Display[] getDisplays(String s){return getDisplays();}
 public interface DisplayListener {void onDisplayAdded(int i);void onDisplayRemoved(int i);void onDisplayChanged(int i);}
}''',
'android.app.Activity': '''public class Activity extends android.content.Context {
 public boolean isFinishing(){return false;} public android.view.Window getWindow(){return new android.view.Window();}
 public android.view.WindowManager getWindowManager(){return new android.view.WindowManager();}
 public java.io.File getExternalFilesDir(String s){return null;}
}''',
'android.app.Presentation': '''public class Presentation implements android.content.DialogInterface {
 final android.content.Context context; public android.view.View content;
 public final android.view.Window window=new android.view.Window();
 public Presentation(android.content.Context c,android.view.Display d,int theme){context=c;}
 public android.content.Context getContext(){return context;} public android.view.Window getWindow(){return window;}
 public void setCancelable(boolean b){} protected void onCreate(android.os.Bundle b){}
 public void setContentView(android.view.View v){content=v;} public void setOnDismissListener(OnDismissListener l){}
 public void show(){} public void dismiss(){} public boolean isShowing(){return true;}
 public android.view.Display getDisplay(){return new android.view.Display();}
}''',
'android.widget.LinearLayout': '''public class LinearLayout extends android.view.ViewGroup {
 public static final int HORIZONTAL=0,VERTICAL=1; public int orientation;
 public LinearLayout(android.content.Context c){super(c);} public void setOrientation(int i){orientation=i;}
 public int getOrientation(){return orientation;} public void setGravity(int g){}
 public static class LayoutParams extends android.view.ViewGroup.LayoutParams {
  public float weight; public int rightMargin,leftMargin;
  public LayoutParams(int w,int h){super(w,h);} public LayoutParams(int w,int h,float f){super(w,h);weight=f;}
 }
}''',
'android.widget.ScrollView': '''public class ScrollView extends android.view.ViewGroup {
 public boolean fill; public ScrollView(android.content.Context c){super(c);}public void setFillViewport(boolean b){fill=b;}
}''',
'android.widget.TextView': '''public class TextView extends android.view.View {
 public CharSequence text=""; public String features=""; public android.graphics.Typeface face;
 public float size,spacing; public int color;
 public final android.graphics.Paint paint=new android.graphics.Paint();
 public TextView(android.content.Context c){super(c);} public android.graphics.Paint getPaint(){return paint;}
 public void setText(CharSequence s){text=s;} public void setTextSize(float s){size=s;paint.size=s;}
 public void setTextColor(int c){color=c;} public void setTypeface(android.graphics.Typeface t){face=t;}
 public void setLetterSpacing(float s){spacing=s;} public void setFontFeatureSettings(String s){features=s;}
}''',
'android.widget.ProgressBar': '''public class ProgressBar extends android.view.View {
 public int maximum,progress; public android.content.res.ColorStateList tint,track;
 public android.graphics.PorterDuff.Mode tintMode,trackMode;
 public ProgressBar(android.content.Context c,Object a,int s){super(c);}
 public void setMax(int m){maximum=m;} public void setProgress(int p){progress=p;}
 public void setProgressTintList(android.content.res.ColorStateList c){tint=c;}
 public void setProgressBackgroundTintList(android.content.res.ColorStateList c){track=c;}
 public void setProgressTintMode(android.graphics.PorterDuff.Mode m){tintMode=m;}
 public void setProgressBackgroundTintMode(android.graphics.PorterDuff.Mode m){trackMode=m;}
}''',
'android.widget.Toast': '''public class Toast {
 public static final int LENGTH_LONG=1; public static Toast makeText(android.content.Context c,String s,int n){return new Toast();}
 public void show(){}
}''',
'android.text.Spanned': 'public interface Spanned extends CharSequence { int SPAN_EXCLUSIVE_EXCLUSIVE=33; }',
'android.text.SpannableString': '''public class SpannableString implements Spanned {
 public final String text;
 public static class Entry {public final Object span;public final int start,end,flags;
  Entry(Object s,int a,int b,int f){span=s;start=a;end=b;flags=f;}}
 public final java.util.List<Entry> spans=new java.util.ArrayList<>();
 public SpannableString(CharSequence s){text=s.toString();}
 public void setSpan(Object s,int a,int b,int f){if(a<0||b>text.length()||a>b)throw new IndexOutOfBoundsException();spans.add(new Entry(s,a,b,f));}
 public int length(){return text.length();}public char charAt(int i){return text.charAt(i);}
 public CharSequence subSequence(int a,int b){return text.substring(a,b);}public String toString(){return text;}
}''',
'android.text.style.ForegroundColorSpan': '''public class ForegroundColorSpan {
 public final int color;public ForegroundColorSpan(int c){color=c;}public int getForegroundColor(){return color;}
}''',
'android.text.style.BackgroundColorSpan': '''public class BackgroundColorSpan {
 public final int color;public BackgroundColorSpan(int c){color=c;}public int getBackgroundColor(){return color;}
}''',
}


def write_stubs(root: Path) -> list[Path]:
    result = []
    for name, code in SOURCES.items():
        package, _ = name.rsplit('.', 1)
        path = root / (name.replace('.', '/') + '.java')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('package ' + package + ';\n' + code + '\n', encoding='utf-8')
        result.append(path)
    return result
