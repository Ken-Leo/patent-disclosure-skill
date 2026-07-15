using System.CommandLine;
using System.Text.Json;
using System.Text.Json.Nodes;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace MiniMaxAIDocx.Core.Commands;

public static class BaseReplaceCommand
{
    static readonly string[] Markers =
    {
        "说明书摘要","摘要附图","权利要求书","说明书",
        "技术领域","背景技术","发明内容","附图说明","具体实施方式","说明书附图"
    };

    public static Command Create()
    {
        var t = new Option<string>("--template"){Required=true, Description="Template DOCX"};
        var o = new Option<string>("--output"){Required=true, Description="Output DOCX"};
        var c = new Option<string>("--content"){Description="JSON content file"};
        var s = new Option<string[]>("--section"){Description="key=value"};

        var cmd = new Command("base-replace","C-2 Base-Replace: in-place text replacement"){t,o,c,s};
        cmd.SetAction(ctx =>
        {
            var tp = ctx.GetValue(t)!; var op = ctx.GetValue(o)!;
            var cp = ctx.GetValue(c); var ss = ctx.GetValue(s);
            if (!File.Exists(tp)){Console.Error.WriteLine($"Not found: {tp}");return;}

            var content = new Dictionary<string, List<string>>();
            if (cp!=null && File.Exists(cp))
                foreach (var kv in JsonNode.Parse(File.ReadAllText(cp))!.AsObject())
                    if (kv.Value is JsonArray arr) content[kv.Key]=arr.Select(x=>x?.ToString()??"").ToList();
                    else content[kv.Key]=kv.Value!.ToString().Split('\n').Select(l=>l.Trim()).Where(l=>l.Length>0).ToList();
            if (ss!=null) foreach (var x in ss){var e=x.IndexOf('=');if(e>0){var k=x[..e];if(!content.ContainsKey(k))content[k]=new();content[k].Add(x[(e+1)..]);}}
            if (content.Count==0){Console.Error.WriteLine("No content.");return;}

            Console.WriteLine($"Sections: {string.Join(", ",content.Keys)}");
            File.Copy(tp, op, true);

            using var doc = WordprocessingDocument.Open(op, true);
            var body = doc.MainDocumentPart?.Document?.Body;
            if (body == null) return;

            foreach (var sn in Markers)
            {
                if (!content.ContainsKey(sn)) continue;
                var lines = content[sn];
                if (lines.Count == 0) continue;

                var all = body.Elements<Paragraph>().ToList();
                Paragraph? m = null;
                foreach (var p in all) if (string.Concat(p.Descendants<Text>().Select(x=>x.Text)) == sn){m=p;break;}
                if (m == null){Console.WriteLine($"  [{sn}] not found");continue;}

                var ms = all.IndexOf(m);
                var ce = all.Count-1;
                for (int j=ms+1;j<all.Count;j++)
                    if (Markers.Contains(string.Concat(all[j].Descendants<Text>().Select(x=>x.Text)))){ce=j-1;break;}

                var old = all.Skip(ms+1).Take(ce-ms).ToList();
                Console.WriteLine($"  [{sn}] {old.Count} -> {lines.Count}");

                int pi;
                for (pi=0; pi<old.Count && pi<lines.Count; pi++)
                {
                    var p = old[pi];
                    // Remove all child elements except pPr
                    var kids = p.ChildElements.ToList();
                    foreach (var ch in kids)
                        if (ch.LocalName != "pPr")
                            ch.Remove();

                    var nr = new Run();
                    var rp = new RunProperties();
                    rp.Append(new FontSize{Val="28"});
                    rp.Append(new FontSizeComplexScript{Val="28"});
                    nr.Append(rp);
                    nr.Append(new Text(lines[pi]){Space=SpaceProcessingModeValues.Preserve});
                    p.Append(nr);
                }

                // Remove extra old paragraphs
                for (int ri=pi; ri<old.Count; ri++) old[ri].Remove();

                // Add extra new paragraphs (format fallback)
                if (pi < lines.Count)
                {
                    all = body.Elements<Paragraph>().ToList();
                    var curM = all.FirstOrDefault(p=>string.Concat(p.Descendants<Text>().Select(x=>x.Text))==sn);
                    if (curM == null) continue;
                    var insAfter = curM;
                    foreach (var p in all)
                        if (all.IndexOf(p) > all.IndexOf(curM)) insAfter = p;
                    for (; pi < lines.Count; pi++)
                    {
                        var np = new Paragraph();
                        var nr = new Run();
                        var rp = new RunProperties();
                        rp.Append(new FontSize{Val="28"});
                        rp.Append(new FontSizeComplexScript{Val="28"});
                        nr.Append(rp);
                        nr.Append(new Text(lines[pi]){Space=SpaceProcessingModeValues.Preserve});
                        np.Append(nr);
                        insAfter.InsertAfterSelf(np);
                        insAfter = np;
                    }
                }
            }

            doc.MainDocumentPart?.Document.Save();
            Console.WriteLine($"\n\u2713 {op}");
        });
        return cmd;
    }
}
