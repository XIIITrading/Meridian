"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const formulaHelpers_1 = require("./formulaHelpers");
const UITypes_1 = __importDefault(require("./UITypes"));
describe('Formula parsing and type validation', () => {
    it('Simple formula', async () => {
        const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
            formula: '1 + 2',
            columns: [],
            clientOrSqlUi: 'mysql2',
            getMeta: async () => ({}),
        });
        expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.NUMERIC);
    });
    it('Formula with IF condition', async () => {
        const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
            formula: 'IF({column}, "Found", BLANK())',
            columns: [
                {
                    id: 'cid',
                    title: 'column',
                    uidt: UITypes_1.default.Number,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: async () => ({}),
        });
        expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.STRING);
    });
    it('Complex formula', async () => {
        const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
            formula: 'SWITCH({column2},"value1",IF({column1}, "Found", BLANK()),"value2", 2)',
            columns: [
                {
                    id: 'id1',
                    title: 'column1',
                    uidt: UITypes_1.default.Number,
                },
                {
                    id: 'id2',
                    title: 'column2',
                    uidt: UITypes_1.default.SingleLineText,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: async () => ({}),
        });
        expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.STRING);
        const result1 = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
            formula: 'SWITCH({column2},"value1",IF({column1}, 1, 2),"value2", 2)',
            columns: [
                {
                    id: 'id1',
                    title: 'column1',
                    uidt: UITypes_1.default.Number,
                },
                {
                    id: 'id2',
                    title: 'column2',
                    uidt: UITypes_1.default.SingleLineText,
                },
            ],
            clientOrSqlUi: 'mysql2',
            getMeta: async () => ({}),
        });
        expect(result1.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.NUMERIC);
    });
    describe('Date and time interaction', () => {
        it('Time - time equals numeric', async () => {
            const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
                formula: '{Time1} - {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Time1',
                        uidt: UITypes_1.default.Time,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes_1.default.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: async () => ({}),
            });
            expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.NUMERIC);
        });
        it('Time - time equals numeric', async () => {
            const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
                formula: '{Time1} - {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Time1',
                        uidt: UITypes_1.default.Time,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes_1.default.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: async () => ({}),
            });
            expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.NUMERIC);
        });
        it('Date + time equals date', async () => {
            const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
                formula: '{Date1} + {Time2}',
                columns: [
                    {
                        id: 'TUrXeTf4JUHdnRvn',
                        title: 'Date1',
                        uidt: UITypes_1.default.Date,
                    },
                    {
                        id: 'J3aD/yLDT2GF6NEB',
                        title: 'Time2',
                        uidt: UITypes_1.default.Time,
                    },
                ],
                clientOrSqlUi: 'pg',
                getMeta: async () => ({}),
            });
            expect(result.dataType).toEqual(formulaHelpers_1.FormulaDataTypes.DATE);
        });
    });
    describe('binary expression', () => {
        it(`& operator will return string`, async () => {
            const result = await (0, formulaHelpers_1.validateFormulaAndExtractTreeWithType)({
                formula: '"Hello" & "World"',
                columns: [],
                clientOrSqlUi: 'pg',
                getMeta: async () => ({}),
            });
            expect(result.dataType).toBe(formulaHelpers_1.FormulaDataTypes.STRING);
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZm9ybXVsYUhlbHBlcnMuc3BlYy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZm9ybXVsYUhlbHBlcnMuc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7OztBQUFBLHFEQUcwQjtBQUMxQix3REFBZ0M7QUFFaEMsUUFBUSxDQUFDLHFDQUFxQyxFQUFFLEdBQUcsRUFBRTtJQUNuRCxFQUFFLENBQUMsZ0JBQWdCLEVBQUUsS0FBSyxJQUFJLEVBQUU7UUFDOUIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFBLHNEQUFxQyxFQUFDO1lBQ3pELE9BQU8sRUFBRSxPQUFPO1lBQ2hCLE9BQU8sRUFBRSxFQUFFO1lBQ1gsYUFBYSxFQUFFLFFBQVE7WUFDdkIsT0FBTyxFQUFFLEtBQUssSUFBSSxFQUFFLENBQUMsQ0FBQyxFQUFFLENBQUM7U0FDMUIsQ0FBQyxDQUFDO1FBRUgsTUFBTSxDQUFDLE1BQU0sQ0FBQyxRQUFRLENBQUMsQ0FBQyxPQUFPLENBQUMsaUNBQWdCLENBQUMsT0FBTyxDQUFDLENBQUM7SUFDNUQsQ0FBQyxDQUFDLENBQUM7SUFFSCxFQUFFLENBQUMsMkJBQTJCLEVBQUUsS0FBSyxJQUFJLEVBQUU7UUFDekMsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFBLHNEQUFxQyxFQUFDO1lBQ3pELE9BQU8sRUFBRSxnQ0FBZ0M7WUFDekMsT0FBTyxFQUFFO2dCQUNQO29CQUNFLEVBQUUsRUFBRSxLQUFLO29CQUNULEtBQUssRUFBRSxRQUFRO29CQUNmLElBQUksRUFBRSxpQkFBTyxDQUFDLE1BQU07aUJBQ3JCO2FBQ0Y7WUFDRCxhQUFhLEVBQUUsUUFBUTtZQUN2QixPQUFPLEVBQUUsS0FBSyxJQUFJLEVBQUUsQ0FBQyxDQUFDLEVBQUUsQ0FBQztTQUMxQixDQUFDLENBQUM7UUFFSCxNQUFNLENBQUMsTUFBTSxDQUFDLFFBQVEsQ0FBQyxDQUFDLE9BQU8sQ0FBQyxpQ0FBZ0IsQ0FBQyxNQUFNLENBQUMsQ0FBQztJ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