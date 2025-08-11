"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.testExtractFilterFromXwhere = void 0;
const filterHelpers_old_1 = require("./filterHelpers_old");
const UITypes_1 = __importDefault(require("./UITypes"));
const testExtractFilterFromXwhere = (title, extractFilterFromXwhere) => {
    describe(title, () => {
        describe('extractFilterFromXwhere', () => {
            it('will parse simple query', async () => {
                const query = '(Title,eq,Hello)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('Hello');
            });
            it('will parse null query', async () => {
                const query = '(Title,eq,)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('');
            });
            it('will parse "in" operator', async () => {
                const query = '(Title,in,1,2,3,4,5)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('in');
                expect(result.filters[0].value).toEqual(['1', '2', '3', '4', '5']);
            });
            it('will map "blank" operator', async () => {
                const queryBlanks = [
                    '(Title,is,blank)',
                    '(Title,isblank)',
                    '(Title,blank)',
                ];
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                for (const blankQuery of queryBlanks) {
                    const result = extractFilterFromXwhere(blankQuery, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('blank');
                    expect(result.filters[0].value).toBeUndefined();
                }
            });
            it('will map "notblank" operator', async () => {
                const queryBlanks = [
                    '(Title,is,notblank)',
                    '(Title,isnotblank)',
                    '(Title,notblank)',
                ];
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                for (const blankQuery of queryBlanks) {
                    const result = extractFilterFromXwhere(blankQuery, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('notblank');
                    expect(result.filters[0].value).toBeUndefined();
                }
            });
            it('will parse value with sub operator', async () => {
                const query = '(Title,eq,oneWeekAgo India)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('oneWeekAgo India');
            });
            describe('datetime', () => {
                it('will parse datetime exactDate', async () => {
                    // most datetime filter need to have suboperator
                    const query = '(Date,lt,exactDate,2025-01-01)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('lt');
                    expect(result.filters[0].comparison_sub_op).toBe('exactDate');
                    expect(result.filters[0].value).toBe('2025-01-01');
                });
                it('will parse datetime oneMonthAgo', async () => {
                    // most datetime filter need to have suboperator
                    const query = '(Date,lt,oneMonthAgo)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('lt');
                    expect(result.filters[0].comparison_sub_op).toBe('oneMonthAgo');
                    expect(result.filters[0].value).toBeUndefined();
                });
                it('will parse datetime isWithin', async () => {
                    // isWithin need to have specific suboperator
                    const query = '(Date,isWithin,pastMonth)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('isWithin');
                    expect(result.filters[0].comparison_sub_op).toBe('pastMonth');
                    expect(result.filters[0].value).toBeUndefined();
                });
                it('will throw error isWithin', async () => {
                    // isWithin need to have specific suboperator
                    const query = '(Date,isWithin,oneMonthAgo)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    expect(() => extractFilterFromXwhere(query, columnAlias, true)).toThrow();
                });
                it('will parse datetime is null', async () => {
                    const query = '(Date,is,null)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('is');
                    expect(result.filters[0].value).toBe(null);
                });
                it('will parse datetime blank', async () => {
                    // datetime need to have suboperator :|
                    const query = '(Date,blank)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes_1.default.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('blank');
                    expect(result.filters[0].value).toBeUndefined();
                });
            });
            describe('json', () => {
                // JSON cannot have filter atm
            });
        });
    });
};
exports.testExtractFilterFromXwhere = testExtractFilterFromXwhere;
(0, exports.testExtractFilterFromXwhere)('filterHelpers_old', filterHelpers_old_1.extractFilterFromXwhere);
describe('filterHelpers_old_specific', () => {
    describe('extractFilterFromXwhere', () => {
        it('will parse comma value', async () => {
            const query = '(Title,eq,Istanbul, India)';
            const columnAlias = {
                Title: {
                    id: 'field1',
                    column_name: 'col1',
                    title: 'Title',
                    uidt: UITypes_1.default.SingleLineText,
                },
            };
            const result = (0, filterHelpers_old_1.extractFilterFromXwhere)(query, columnAlias);
            expect(result.filters).toBeDefined();
            expect(result.filters.length).toBe(1);
            expect(result.filters[0].comparison_op).toBe('eq');
            expect(result.filters[0].value).toBe('Istanbul, India');
        });
        describe('logical', () => {
            it('will parse basic logical query', () => {
                // isWithin need to have specific suboperator :|
                const query = '(Date,isWithin,pastMonth)~and(Name,like,Hello)';
                const columnAlias = {
                    Date: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Date',
                        uidt: UITypes_1.default.DateTime,
                    },
                    Name: {
                        id: 'field2',
                        column_name: 'col2',
                        title: 'Name',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = (0, filterHelpers_old_1.extractFilterFromXwhere)(query, columnAlias);
                expect(result).toBeDefined();
                expect(result.filters.length).toBe(2);
                expect(result.filters[1].logical_op).toBe('and');
            });
            it('will parse nested logical query', () => {
                // isWithin need to have specific suboperator :|
                const query = '(Date,isWithin,pastMonth)~or((Name,like,Hello)~and(Name,like,World))';
                const columnAlias = {
                    Date: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Date',
                        uidt: UITypes_1.default.DateTime,
                    },
                    Name: {
                        id: 'field2',
                        column_name: 'col2',
                        title: 'Name',
                        uidt: UITypes_1.default.SingleLineText,
                    },
                };
                const result = (0, filterHelpers_old_1.extractFilterFromXwhere)(query, columnAlias);
                expect(result).toBeDefined();
                expect(result.filters.length).toBe(2);
                expect(result.filters[1].logical_op).toBe('or');
            });
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVyc19vbGQuc3BlYy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZmlsdGVySGVscGVyc19vbGQuc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7Ozs7QUFDQSwyREFBOEQ7QUFDOUQsd0RBQWdDO0FBRXpCLE1BQU0sMkJBQTJCLEdBQUcsQ0FDekMsS0FBYSxFQUNiLHVCQUk2QyxFQUM3QyxFQUFFO0lBQ0YsUUFBUSxDQUFDLEtBQUssRUFBRSxHQUFHLEVBQUU7UUFDbkIsUUFBUSxDQUFDLHlCQUF5QixFQUFFLEdBQUcsRUFBRTtZQUN2QyxFQUFFLENBQUMseUJBQXlCLEVBQUUsS0FBSyxJQUFJLEVBQUU7Z0JBQ3ZDLE1BQU0sS0FBSyxHQUFHLGtCQUFrQixDQUFDO2dCQUNqQyxNQUFNLFdBQVcsR0FBK0I7b0JBQzlDLEtBQUssRUFBRTt3QkFDTCxFQUFFLEVBQUUsUUFBUTt3QkFDWixXQUFXLEVBQUUsTUFBTTt3QkFDbkIsS0FBSyxFQUFFLE9BQU87d0JBQ2QsSUFBSSxFQUFFLGlCQUFPLENBQUMsY0FBYztxQkFDN0I7aUJBQ0YsQ0FBQztnQkFDRixNQUFNLE1BQU0sR0FBRyx1QkFBdUIsQ0FBQyxLQUFLLEVBQUUsV0FBVyxDQUFDLENBQUM7Z0JBQzNELE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsV0FBVyxFQUFFLENBQUM7Z0JBQ3JDLE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLE1BQU0sQ0FBQyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQztnQkFDdEMsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsQ0FBQyxDQUFDLENBQUMsYUFBYSxDQUFDLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxDQUFDO2dCQUNuRCxNQUFNLENBQUMsTUFBTSxDQUFDLE9BQU8sQ0FBQyxDQUFDLENBQUMsQ0FBQyxLQUFLLENBQUMsQ0FBQyxJQUFJLENBQUMsT0FB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