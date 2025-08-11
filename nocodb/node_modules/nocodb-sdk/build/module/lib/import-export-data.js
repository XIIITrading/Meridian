export var SupportedExportCharset;
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
})(SupportedExportCharset || (SupportedExportCharset = {}));
export const charsetOptions = [
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
export const charsetOptionsMap = charsetOptions.reduce((acc, curr) => {
    acc[curr.value] = curr;
    return acc;
}, {});
export var CsvColumnSeparator;
(function (CsvColumnSeparator) {
    CsvColumnSeparator[","] = ",";
    CsvColumnSeparator[";"] = ";";
    CsvColumnSeparator["|"] = "|";
    CsvColumnSeparator["tab"] = "\t";
})(CsvColumnSeparator || (CsvColumnSeparator = {}));
export const csvColumnSeparatorOptions = [
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW1wb3J0LWV4cG9ydC1kYXRhLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9pbXBvcnQtZXhwb3J0LWRhdGEudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsTUFBTSxDQUFOLElBQVksc0JBa0NYO0FBbENELFdBQVksc0JBQXNCO0lBQ2hDLHlDQUFpQixDQUFBO0lBQ2pCLG1EQUEyQixDQUFBO0lBQzNCLHVEQUErQixDQUFBO0lBQy9CLG1EQUEyQixDQUFBO0lBQzNCLHVEQUErQixDQUFBO0lBQy9CLHFEQUE2QixDQUFBO0lBQzdCLG1EQUEyQixDQUFBO0lBQzNCLHVEQUErQixDQUFBO0lBQy9CLHFDQUFhLENBQUE7SUFDYiw2Q0FBcUIsQ0FBQTtJQUNyQix1Q0FBZSxDQUFBO0lBQ2YsMkNBQW1CLENBQUE7SUFDbkIsMkNBQW1CLENBQUE7SUFDbkIsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IsMkRBQW1DLENBQUE7SUFDbkMsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IsMkNBQW1CLENBQUE7SUFDbkIscURBQTZCLENBQUE7SUFDN0IsaURBQXlCLENBQUE7SUFDekIsMkNBQW1CLENBQUE7SUFDbkIsaURBQXlCLENBQUE7SUFDekIscURBQTZCLENBQUE7SUFDN0IscURBQTZCLENBQUE7SUFDN0IscURBQTZCLENBQUE7SUFDN0IsdURBQStCLENBQUE7SUFDL0IsdURBQStCLENBQUE7SUFDL0IsbURBQTJCLENBQUE7SUFDM0IsdURBQStCLENBQUE7SUFDL0IsbURBQTJCLENBQUE7QUFDN0IsQ0FBQyxFQWxDVyxzQkFBc0IsS0FBdEIsc0JBQXNCLFFBa0NqQztBQVFELE1BQU0sQ0FBQyxNQUFNLGNBQWMsR0FBeUI7SUFDbEQ7UUFDRSxLQUFLLEVBQUUsaUJBQWlCO1FBQ3hCLEtBQUssRUFBRSxzQkFBc0IsQ0FB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