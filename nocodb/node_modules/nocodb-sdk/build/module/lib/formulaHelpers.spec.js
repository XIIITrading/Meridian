var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { FormulaDataTypes, validateFormulaAndExtractTreeWithType, } from './formulaHelpers';
import UITypes from './UITypes';
describe('Formula parsing and type validation', () => {
    it('Simple formula', () => __awaiter(void 0, void 0, void 0, function* () {
        const result = yield validateFormulaAndExtractTreeWithType({
            formula: '1 + 2',
            columns: [],
            clientOrSqlUi: 'mysql2',
            getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
        });
        expect(result.dataType).toEqual(FormulaDataTypes.NUMERIC);
    }));
    it('Formula with IF condition', () => __awaiter(void 0, void 0, void 0, function* () {
        const result = yield validateFormulaAndExtractTreeWithType({
            formula: 'IF({column}, "Found", BLANK())',
            columns: [
                {
                    id: 'cid',
                    title: 'column',
                    uidt: UITypes.Number,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
        });
        expect(result.dataType).toEqual(FormulaDataTypes.STRING);
    }));
    it('Complex formula', () => __awaiter(void 0, void 0, void 0, function* () {
        const result = yield validateFormulaAndExtractTreeWithType({
            formula: 'SWITCH({column2},"value1",IF({column1}, "Found", BLANK()),"value2", 2)',
            columns: [
                {
                    id: 'id1',
                    title: 'column1',
                    uidt: UITypes.Number,
                },
                {
                    id: 'id2',
                    title: 'column2',
                    uidt: UITypes.SingleLineText,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
        });
        expect(result.dataType).toEqual(FormulaDataTypes.STRING);
        const result1 = yield validateFormulaAndExtractTreeWithType({
            formula: 'SWITCH({column2},"value1",IF({column1}, 1, 2),"value2", 2)',
            columns: [
                {
                    id: 'id1',
                    title: 'column1',
                    uidt: UITypes.Number,
                },
                {
                    id: 'id2',
                    title: 'column2',
                    uidt: UITypes.SingleLineText,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
        });
        expect(result1.dataType).toEqual(FormulaDataTypes.NUMERIC);
    }));
    describe('Date and time interaction', () => {
        it('Time - time equals numeric', () => __awaiter(void 0, void 0, void 0, function* () {
            const result = yield validateFormulaAndExtractTreeWithType({
                formula: '{Time1} - {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Time1',
                        uidt: UITypes.Time,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
            });
            expect(result.dataType).toEqual(FormulaDataTypes.NUMERIC);
        }));
        it('Time - time equals numeric', () => __awaiter(void 0, void 0, void 0, function* () {
            const result = yield validateFormulaAndExtractTreeWithType({
                formula: '{Time1} - {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Time1',
                        uidt: UITypes.Time,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
            });
            expect(result.dataType).toEqual(FormulaDataTypes.NUMERIC);
        }));
        it('Date + time equals date', () => __awaiter(void 0, void 0, void 0, function* () {
            const result = yield validateFormulaAndExtractTreeWithType({
                formula: '{Date1} + {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Date1',
                        uidt: UITypes.Date,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
            });
            expect(result.dataType).toEqual(FormulaDataTypes.DATE);
        }));
    });
    describe('binary expression', () => {
        it(`& operator will return string`, () => __awaiter(void 0, void 0, void 0, function* () {
            const result = yield validateFormulaAndExtractTreeWithType({
                formula: '"Hello" & "World"',
                columns: [],
                clientOrSqlUi: 'pg',
                getMeta: () => __awaiter(void 0, void 0, void 0, function* () { return ({}); }),
            });
            expect(result.dataType).toBe(FormulaDataTypes.STRING);
        }));
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZm9ybXVsYUhlbHBlcnMuc3BlYy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZm9ybXVsYUhlbHBlcnMuc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7QUFBQSxPQUFPLEVBQ0wsZ0JBQWdCLEVBQ2hCLHFDQUFxQyxHQUN0QyxNQUFNLGtCQUFrQixDQUFDO0FBQzFCLE9BQU8sT0FBTyxNQUFNLFdBQVcsQ0FBQztBQUVoQyxRQUFRLENBQUMscUNBQXFDLEVBQUUsR0FBRyxFQUFFO0lBQ25ELEVBQUUsQ0FBQyxnQkFBZ0IsRUFBRSxHQUFTLEVBQUU7UUFDOUIsTUFBTSxNQUFNLEdBQUcsTUFBTSxxQ0FBcUMsQ0FBQztZQUN6RCxPQUFPLEVBQUUsT0FBTztZQUNoQixPQUFPLEVBQUUsRUFBRTtZQUNYLGFBQWEsRUFBRSxRQUFRO1lBQ3ZCLE9BQU8sRUFBRSxHQUFTLEVBQUUsa0RBQUMsT0FBQSxDQUFDLEVBQUUsQ0FBQyxDQUFBLEdBQUE7U0FDMUIsQ0FBQyxDQUFDO1FBRUgsTUFBTSxDQUFDLE1BQU0sQ0FBQyxRQUFRLENBQUMsQ0FBQyxPQUFPLENBQUMsZ0JBQWdCLENBQUMsT0FBTyxDQUFDLENBQUM7SUFDNUQsQ0FBQyxDQUFBLENBQUMsQ0FBQztJQUVILEVBQUUsQ0FBQywyQkFBMkIsRUFBRSxHQUFTLEVBQUU7UUFDekMsTUFBTSxNQUFNLEdBQUcsTUFBTSxxQ0FBcUMsQ0FBQztZQUN6RCxPQUFPLEVBQUUsZ0NBQWdDO1lBQ3pDLE9BQU8sRUFBRTtnQkFDUDtvQkFDRSxFQUFFLEVBQUUsS0FBSztvQkFDVCxLQUFLLEVBQUUsUUFBUTtvQkFDZixJQUFJLEVBQUUsT0FBTyxDQUFDLE1BQU07aUJBQ3JCO2FBQ0Y7WUFDRCxhQUFhLEVBQUUsUUFBUTtZQUN2QixPQUFPLEVBQUUsR0FBUyxFQUFFLGtEQUFDLE9BQUEsQ0FBQyxFQUFFLENBQUMsQ0FBQSxHQUFBO1NBQzFCLENBQUMsQ0FBQztRQUVI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