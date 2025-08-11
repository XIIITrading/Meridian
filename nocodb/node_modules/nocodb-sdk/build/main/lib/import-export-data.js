"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.csvColumnSeparatorOptions = exports.CsvColumnSeparator = exports.charsetOptionsMap = exports.charsetOptions = exports.SupportedExportCharset = void 0;
var SupportedExportCharset;
(function (SupportedExportCharset) {
    SupportedExportCharset["utf-8"] = "utf-8";
    SupportedExportCharset["iso-8859-6"] = "iso-8859-6";
    SupportedExportCharset["windows-1256"] = "windows-1256";
    SupportedExportCharset["iso-8859-4"] = "iso-8859-4";
    SupportedExportCharset["windows-1257"] = "windows-1257";
    SupportedExportCharset["iso-8859-14"] = "iso-8859-14";
    SupportedExportCharset["iso-8859-2"] = "iso-8859-2";
    SupportedExportCharset["windows-1250"] = "windows-1250";
    SupportedExportCharset["gbk"] = "gbk";
    SupportedExportCharset["gb18030"] = "gb18030";
    SupportedExportCharset["big5"] = "big5";
    SupportedExportCharset["koi8-r"] = "koi8-r";
    SupportedExportCharset["koi8-u"] = "koi8-u";
    SupportedExportCharset["iso-8859-5"] = "iso-8859-5";
    SupportedExportCharset["windows-1251"] = "windows-1251";
    SupportedExportCharset["x-mac-cyrillic"] = "x-mac-cyrillic";
    SupportedExportCharset["iso-8859-7"] = "iso-8859-7";
    SupportedExportCharset["windows-1253"] = "windows-1253";
    SupportedExportCharset["iso-8859-8"] = "iso-8859-8";
    SupportedExportCharset["windows-1255"] = "windows-1255";
    SupportedExportCharset["euc-jp"] = "euc-jp";
    SupportedExportCharset["iso-2022-jp"] = "iso-2022-jp";
    SupportedExportCharset["shift-jis"] = "shift-jis";
    SupportedExportCharset["euc-kr"] = "euc-kr";
    SupportedExportCharset["macintosh"] = "macintosh";
    SupportedExportCharset["iso-8859-10"] = "iso-8859-10";
    SupportedExportCharset["iso-8859-16"] = "iso-8859-16";
    SupportedExportCharset["windows-874"] = "windows-874";
    SupportedExportCharset["windows-1254"] = "windows-1254";
    SupportedExportCharset["windows-1258"] = "windows-1258";
    SupportedExportCharset["iso-8859-1"] = "iso-8859-1";
    SupportedExportCharset["windows-1252"] = "windows-1252";
    SupportedExportCharset["iso-8859-3"] = "iso-8859-3";
})(SupportedExportCharset || (exports.SupportedExportCharset = SupportedExportCharset = {}));
exports.charsetOptions = [
    {
        label: 'Unicode (UTF-8)',
        value: SupportedExportCharset['utf-8'],
        sortLabel: 'UTF-8',
    },
    {
        label: 'Arabic (ISO-8859-6)',
        value: SupportedExportCharset['iso-8859-6'],
        sortLabel: 'ISO-8859-6',
    },
    {
        label: 'Arabic (Windows-1256)',
        value: SupportedExportCharset['windows-1256'],
        sortLabel: 'Windows-1256',
    },
    {
        label: 'Baltic (ISO-8859-4)',
        value: SupportedExportCharset['iso-8859-4'],
        sortLabel: 'ISO-8859-4',
    },
    {
        label: 'Baltic (windows-1257)',
        value: SupportedExportCharset['windows-1257'],
        sortLabel: 'Windows-1257',
    },
    {
        label: 'Celtic (ISO-8859-14)',
        value: SupportedExportCharset['iso-8859-14'],
        sortLabel: 'ISO-8859-14',
    },
    {
        label: 'Central European (ISO-8859-2)',
        value: SupportedExportCharset['iso-8859-2'],
        sortLabel: 'ISO-8859-2',
    },
    {
        label: 'Central European (Windows-1250)',
        value: SupportedExportCharset['windows-1250'],
        sortLabel: 'Windows-1250',
    },
    {
        label: 'Chinese, Simplified (GBK)',
        value: SupportedExportCharset['gbk'],
        sortLabel: 'GBK',
    },
    {
        label: 'Chinese (GB18030)',
        value: SupportedExportCharset['gb18030'],
        sortLabel: 'GB18030',
    },
    {
        label: 'Chinese Traditional (Big5)',
        value: SupportedExportCharset['big5'],
        sortLabel: 'Big5',
    },
    {
        label: 'Cyrillic (KOI8-R)',
        value: SupportedExportCharset['koi8-r'],
        sortLabel: 'KOI8-R',
    },
    {
        label: 'Cyrillic (KOI8-U)',
        value: SupportedExportCharset['koi8-u'],
        sortLabel: 'KOI8-U',
    },
    {
        label: 'Cyrillic (ISO-8859-5)',
        value: SupportedExportCharset['iso-8859-5'],
        sortLabel: 'ISO-8859-5',
    },
    {
        label: 'Cyrillic (Windows-1251)',
        value: SupportedExportCharset['windows-1251'],
        sortLabel: 'Windows-1251',
    },
    {
        label: 'Cyrillic Mac OS (x-mac-cyrillic)',
        value: SupportedExportCharset['x-mac-cyrillic'],
        sortLabel: 'x-mac-cyrillic',
    },
    {
        label: 'Greek (ISO-8859-7)',
        value: SupportedExportCharset['iso-8859-7'],
        sortLabel: 'ISO-8859-7',
    },
    {
        label: 'Greek (Windows-1253)',
        value: SupportedExportCharset['windows-1253'],
        sortLabel: 'Windows-1253',
    },
    {
        label: 'Hebrew (ISO-8859-8)',
        value: SupportedExportCharset['iso-8859-8'],
        sortLabel: 'ISO-8859-8',
    },
    {
        label: 'Hebrew (Windows-1255)',
        value: SupportedExportCharset['windows-1255'],
        sortLabel: 'Windows-1255',
    },
    {
        label: 'Japanese (EUC-JP)',
        value: SupportedExportCharset['euc-jp'],
        sortLabel: 'EUC-JP',
    },
    {
        label: 'Japanese (ISO-2022-JP)',
        value: SupportedExportCharset['iso-2022-jp'],
        sortLabel: 'ISO-2022-JP',
    },
    {
        label: 'Japanese (Shift-JIS)',
        value: SupportedExportCharset['shift-jis'],
        sortLabel: 'Shift-JIS',
    },
    {
        label: 'Korean (EUC-KR)',
        value: SupportedExportCharset['euc-kr'],
        sortLabel: 'EUC-KR',
    },
    {
        label: 'Macintosh',
        value: SupportedExportCharset['macintosh'],
        sortLabel: 'Macintosh',
    }, // No parentheses
    {
        label: 'Nordic (ISO-8859-10)',
        value: SupportedExportCharset['iso-8859-10'],
        sortLabel: 'ISO-8859-10',
    },
    {
        label: 'South-Eastern European (ISO-8859-16)',
        value: SupportedExportCharset['iso-8859-16'],
        sortLabel: 'ISO-8859-16',
    },
    {
        label: 'Thai (Windows-874)',
        value: SupportedExportCharset['windows-874'],
        sortLabel: 'Windows-874',
    },
    {
        label: 'Turkish (Windows-1254)',
        value: SupportedExportCharset['windows-1254'],
        sortLabel: 'Windows-1254',
    },
    {
        label: 'Vietnamese (Windows-1258)',
        value: SupportedExportCharset['windows-1258'],
        sortLabel: 'Windows-1258',
    },
    {
        label: 'Western European (ISO-8859-1)',
        value: SupportedExportCharset['iso-8859-1'],
        sortLabel: 'ISO-8859-1',
    },
    {
        label: 'Western European (Windows-1252)',
        value: SupportedExportCharset['windows-1252'],
        sortLabel: 'Windows-1252',
    },
    {
        label: 'Latin 3 (ISO-8859-3)',
        value: SupportedExportCharset['iso-8859-3'],
        sortLabel: 'ISO-8859-3',
    },
];
exports.charsetOptionsMap = exports.charsetOptions.reduce((acc, curr) => {
    acc[curr.value] = curr;
    return acc;
}, {});
var CsvColumnSeparator;
(function (CsvColumnSeparator) {
    CsvColumnSeparator[","] = ",";
    CsvColumnSeparator[";"] = ";";
    CsvColumnSeparator["|"] = "|";
    CsvColumnSeparator["tab"] = "\t";
})(CsvColumnSeparator || (exports.CsvColumnSeparator = CsvColumnSeparator = {}));
exports.csvColumnSeparatorOptions = [
    {
        label: 'Comma (,)',
        value: CsvColumnSeparator[','],
    },
    {
        label: 'Semi-colon (;)',
        value: CsvColumnSeparator[';'],
    },
    {
        label: 'Pipe (|)',
        value: CsvColumnSeparator['|'],
    },
    {
        label: '<Tab>',
        value: CsvColumnSeparator['tab'],
    },
];
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW1wb3J0LWV4cG9ydC1kYXRhLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9pbXBvcnQtZXhwb3J0LWRhdGEudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsSUFBWSxzQkFrQ1g7QUFsQ0QsV0FBWSxzQkFBc0I7SUFDaEMseUNBQWlCLENBQUE7SUFDakIsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IscURBQTZCLENBQUE7SUFDN0IsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IscUNBQWEsQ0FBQTtJQUNiLDZDQUFxQixDQUFBO0lBQ3JCLHVDQUFlLENBQUE7SUFDZiwyQ0FBbUIsQ0FBQTtJQUNuQiwyQ0FBbUIsQ0FBQTtJQUNuQixtREFBMkIsQ0FBQTtJQUMzQix1REFBK0IsQ0FBQTtJQUMvQiwyREFBbUMsQ0FBQTtJQUNuQyxtREFBMkIsQ0FBQTtJQUMzQix1REFBK0IsQ0FBQTtJQUMvQixtREFBMkIsQ0FBQTtJQUMzQix1REFBK0IsQ0FBQTtJQUMvQiwyQ0FBbUIsQ0FBQTtJQUNuQixxREFBNkIsQ0FBQTtJQUM3QixpREFBeUIsQ0FBQTtJQUN6QiwyQ0FBbUIsQ0FBQTtJQUNuQixpREFBeUIsQ0FBQTtJQUN6QixxREFBNkIsQ0FBQTtJQUM3QixxREFBNkIsQ0FBQTtJQUM3QixxREFBNkIsQ0FBQTtJQUM3Qix1REFBK0IsQ0FBQTtJQUMvQix1REFBK0IsQ0FBQTtJQUMvQixtREFBMkIsQ0FBQTtJQUMzQix1REFBK0IsQ0FBQTtJQUMvQixtREFBMkIsQ0FBQTtBQUM3QixDQUFDLEVBbENXLHNCQUFzQixzQ0FBdEIsc0JBQXNCLFFBa0NqQztBQVFZLFFBQUEsY0FBYyxHQUF5QjtJQUNsRDtRQUNFLEtBQUssRUFBRSxpQkFBaUI7UUFDeEIsS0FBSyxFQUFFLHNCQUFzQixDQUFDLE9BQU8sQ0FBQztRQUN0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