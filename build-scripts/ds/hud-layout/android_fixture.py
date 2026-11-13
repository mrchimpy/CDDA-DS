"""Extend the existing host substitutes privately; not a real Android layout engine."""
import importlib.util
from pathlib import Path


def write_stubs(root: Path, original: Path) -> list[Path]:
    spec = importlib.util.spec_from_file_location('layout_base_android_substitutes', original)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sources = dict(module.SOURCES)  # Do not mutate the older experiment's substitutes.

    def change(name: str, old: str, new: str):
        if sources[name].count(old) != 1:
            raise AssertionError(f'Android substitute anchor changed: {name}: {old}')
        sources[name] = sources[name].replace(old, new, 1)

    sources['android/graphics/Paint.java'] = '''package android.graphics;
public class Paint {
 public static float widthScale=1.0f;
 public float size=16f;
 // Deliberately simple modeled widths, not actual Terminus/Android glyph measurements.
 public float measureText(String text) { return text.codePointCount(0,text.length())*size*0.5f*widthScale; }
}'''
    change('android/widget/TextView.java', 'public String text="",features="";',
           'public final android.graphics.Paint paint=new android.graphics.Paint();\n public android.graphics.Paint getPaint(){return paint;}\n public String text="",features="";')
    change('android/widget/TextView.java', 'public void setTextSize(float s){size=s;}',
           'public void setTextSize(float s){size=s;paint.size=s;}')
    change('android/view/View.java', ' public int[] padding;', ''' public ViewGroup.LayoutParams params;
 public ViewGroup parent;
 public int setParamsCalls;
 public void setLayoutParams(ViewGroup.LayoutParams p){params=p;setParamsCalls++;}
 public ViewGroup.LayoutParams getLayoutParams(){return params;}
 public int getPaddingLeft(){return padding==null ? 0 : padding[0];}
 public int getPaddingRight(){return padding==null ? 0 : padding[2];}
 protected void onMeasure(int w,int h){}
 public final void measure(int w,int h){onMeasure(w,h);}
 public static final class MeasureSpec {
  public static final int UNSPECIFIED=0, EXACTLY=0x40000000, AT_MOST=0x80000000;
  public static int getSize(int spec){return spec&0x3fffffff;}
  public static int getMode(int spec){return spec&0xc0000000;}
  public static int makeMeasureSpec(int size,int mode){return (size&0x3fffffff)|mode;}
 }
 public int[] padding;''')
    change('android/view/ViewGroup.java', 'public void addView(View v){children.add(v);}',
           'public void addView(View v){if(v.parent!=null)throw new IllegalStateException("Already parented");v.parent=this;children.add(v);}')
    change('android/view/ViewGroup.java', 'public void addView(View v,LayoutParams p){children.add(v);}',
           'public void addView(View v,LayoutParams p){v.setLayoutParams(p);addView(v);}')
    change('android/widget/LinearLayout.java', 'public static final int VERTICAL=1;',
           'public static final int HORIZONTAL=0, VERTICAL=1; public int orientation;')
    change('android/widget/LinearLayout.java', 'public void setOrientation(int i){}',
           'public void setOrientation(int i){orientation=i;} public int getOrientation(){return orientation;}')
    change('android/widget/LinearLayout.java', 'public int rightMargin;', 'public int rightMargin,leftMargin;')
    result = []
    for relative, source in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source + '\n', encoding='utf-8')
        result.append(path)
    return result
