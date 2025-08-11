export declare enum SupportedExportCharset {
    'utf-8' = "utf-8",
    'iso-8859-6' = "iso-8859-6",
    'windows-1256' = "windows-1256",
    'iso-8859-4' = "iso-8859-4",
    'windows-1257' = "windows-1257",
    'iso-8859-14' = "iso-8859-14",
    'iso-8859-2' = "iso-8859-2",
    'windows-1250' = "windows-1250",
    'gbk' = "gbk",
    'gb18030' = "gb18030",
    'big5' = "big5",
    'koi8-r' = "koi8-r",
    'koi8-u' = "koi8-u",
    'iso-8859-5' = "iso-8859-5",
    'windows-1251' = "windows-1251",
    'x-mac-cyrillic' = "x-mac-cyrillic",
    'iso-8859-7' = "iso-8859-7",
    'windows-1253' = "windows-1253",
    'iso-8859-8' = "iso-8859-8",
    'windows-1255' = "windows-1255",
    'euc-jp' = "euc-jp",
    'iso-2022-jp' = "iso-2022-jp",
    'shift-jis' = "shift-jis",
    'euc-kr' = "euc-kr",
    'macintosh' = "macintosh",
    'iso-8859-10' = "iso-8859-10",
    'iso-8859-16' = "iso-8859-16",
    'windows-874' = "windows-874",
    'windows-1254' = "windows-1254",
    'windows-1258' = "windows-1258",
    'iso-8859-1' = "iso-8859-1",
    'windows-1252' = "windows-1252",
    'iso-8859-3' = "iso-8859-3"
}
export interface CharsetOptionsType {
    label: string;
    sortLabel: string;
    value: SupportedExportCharset;
}
export declare const charsetOptions: CharsetOptionsType[];
export declare const charsetOptionsMap: Record<string, CharsetOptionsType>;
export declare enum CsvColumnSeparator {
    ',' = ",",
    ';' = ";",
    '|' = "|",
    'tab' = "\t"
}
export declare const csvColumnSeparatorOptions: {
    label: string;
    value: CsvColumnSeparator;
}[];
