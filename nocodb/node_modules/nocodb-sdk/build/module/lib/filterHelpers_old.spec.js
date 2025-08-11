var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { extractFilterFromXwhere } from './filterHelpers_old';
import UITypes from './UITypes';
export const testExtractFilterFromXwhere = (title, extractFilterFromXwhere) => {
    describe(title, () => {
        describe('extractFilterFromXwhere', () => {
            it('will parse simple query', () => __awaiter(void 0, void 0, void 0, function* () {
                const query = '(Title,eq,Hello)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('Hello');
            }));
            it('will parse null query', () => __awaiter(void 0, void 0, void 0, function* () {
                const query = '(Title,eq,)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('');
            }));
            it('will parse "in" operator', () => __awaiter(void 0, void 0, void 0, function* () {
                const query = '(Title,in,1,2,3,4,5)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('in');
                expect(result.filters[0].value).toEqual(['1', '2', '3', '4', '5']);
            }));
            it('will map "blank" operator', () => __awaiter(void 0, void 0, void 0, function* () {
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
                        uidt: UITypes.SingleLineText,
                    },
                };
                for (const blankQuery of queryBlanks) {
                    const result = extractFilterFromXwhere(blankQuery, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('blank');
                    expect(result.filters[0].value).toBeUndefined();
                }
            }));
            it('will map "notblank" operator', () => __awaiter(void 0, void 0, void 0, function* () {
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
                        uidt: UITypes.SingleLineText,
                    },
                };
                for (const blankQuery of queryBlanks) {
                    const result = extractFilterFromXwhere(blankQuery, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('notblank');
                    expect(result.filters[0].value).toBeUndefined();
                }
            }));
            it('will parse value with sub operator', () => __awaiter(void 0, void 0, void 0, function* () {
                const query = '(Title,eq,oneWeekAgo India)';
                const columnAlias = {
                    Title: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Title',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect(result.filters[0].comparison_op).toBe('eq');
                expect(result.filters[0].value).toBe('oneWeekAgo India');
            }));
            describe('datetime', () => {
                it('will parse datetime exactDate', () => __awaiter(void 0, void 0, void 0, function* () {
                    // most datetime filter need to have suboperator
                    const query = '(Date,lt,exactDate,2025-01-01)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('lt');
                    expect(result.filters[0].comparison_sub_op).toBe('exactDate');
                    expect(result.filters[0].value).toBe('2025-01-01');
                }));
                it('will parse datetime oneMonthAgo', () => __awaiter(void 0, void 0, void 0, function* () {
                    // most datetime filter need to have suboperator
                    const query = '(Date,lt,oneMonthAgo)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('lt');
                    expect(result.filters[0].comparison_sub_op).toBe('oneMonthAgo');
                    expect(result.filters[0].value).toBeUndefined();
                }));
                it('will parse datetime isWithin', () => __awaiter(void 0, void 0, void 0, function* () {
                    // isWithin need to have specific suboperator
                    const query = '(Date,isWithin,pastMonth)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('isWithin');
                    expect(result.filters[0].comparison_sub_op).toBe('pastMonth');
                    expect(result.filters[0].value).toBeUndefined();
                }));
                it('will throw error isWithin', () => __awaiter(void 0, void 0, void 0, function* () {
                    // isWithin need to have specific suboperator
                    const query = '(Date,isWithin,oneMonthAgo)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    expect(() => extractFilterFromXwhere(query, columnAlias, true)).toThrow();
                }));
                it('will parse datetime is null', () => __awaiter(void 0, void 0, void 0, function* () {
                    const query = '(Date,is,null)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('is');
                    expect(result.filters[0].value).toBe(null);
                }));
                it('will parse datetime blank', () => __awaiter(void 0, void 0, void 0, function* () {
                    // datetime need to have suboperator :|
                    const query = '(Date,blank)';
                    const columnAlias = {
                        Date: {
                            id: 'field1',
                            column_name: 'col1',
                            title: 'Date',
                            uidt: UITypes.DateTime,
                        },
                    };
                    const result = extractFilterFromXwhere(query, columnAlias);
                    expect(result.filters).toBeDefined();
                    expect(result.filters.length).toBe(1);
                    expect(result.filters[0].comparison_op).toBe('blank');
                    expect(result.filters[0].value).toBeUndefined();
                }));
            });
            describe('json', () => {
                // JSON cannot have filter atm
            });
        });
    });
};
testExtractFilterFromXwhere('filterHelpers_old', extractFilterFromXwhere);
describe('filterHelpers_old_specific', () => {
    describe('extractFilterFromXwhere', () => {
        it('will parse comma value', () => __awaiter(void 0, void 0, void 0, function* () {
            const query = '(Title,eq,Istanbul, India)';
            const columnAlias = {
                Title: {
                    id: 'field1',
                    column_name: 'col1',
                    title: 'Title',
                    uidt: UITypes.SingleLineText,
                },
            };
            const result = extractFilterFromXwhere(query, columnAlias);
            expect(result.filters).toBeDefined();
            expect(result.filters.length).toBe(1);
            expect(result.filters[0].comparison_op).toBe('eq');
            expect(result.filters[0].value).toBe('Istanbul, India');
        }));
        describe('logical', () => {
            it('will parse basic logical query', () => {
                // isWithin need to have specific suboperator :|
                const query = '(Date,isWithin,pastMonth)~and(Name,like,Hello)';
                const columnAlias = {
                    Date: {
                        id: 'field1',
                        column_name: 'col1',
                        title: 'Date',
                        uidt: UITypes.DateTime,
                    },
                    Name: {
                        id: 'field2',
                        column_name: 'col2',
                        title: 'Name',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
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
                        uidt: UITypes.DateTime,
                    },
                    Name: {
                        id: 'field2',
                        column_name: 'col2',
                        title: 'Name',
                        uidt: UITypes.SingleLineText,
                    },
                };
                const result = extractFilterFromXwhere(query, columnAlias);
                expect(result).toBeDefined();
                expect(result.filters.length).toBe(2);
                expect(result.filters[1].logical_op).toBe('or');
            });
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVyc19vbGQuc3BlYy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZmlsdGVySGVscGVyc19vbGQuc3BlYy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7QUFDQSxPQUFPLEVBQUUsdUJBQXVCLEVBQUUsTUFBTSxxQkFBcUIsQ0FBQztBQUM5RCxPQUFPLE9BQU8sTUFBTSxXQUFXLENBQUM7QUFFaEMsTUFBTSxDQUFDLE1BQU0sMkJBQTJCLEdBQUcsQ0FDekMsS0FBYSxFQUNiLHVCQUk2QyxFQUM3QyxFQUFFO0lBQ0YsUUFBUSxDQUFDLEtBQUssRUFBRSxHQUFHLEVBQUU7UUFDbkIsUUFBUSxDQUFDLHlCQUF5QixFQUFFLEdBQUcsRUFBRTtZQUN2QyxFQUFFLENBQUMseUJBQXlCLEVBQUUsR0FBUyxFQUFFO2dCQUN2QyxNQUFNLEtBQUssR0FBRyxrQkFBa0IsQ0FBQztnQkFDakMsTUFBTSxXQUFXLEdBQStCO29CQUM5QyxLQUFLLEVBQUU7d0JBQ0wsRUFBRSxFQUFFLFFBQVE7d0JBQ1osV0FBVyxFQUFFLE1BQU07d0JBQ25CLEtBQUssRUFBRSxPQUFPO3dCQUNkLElBQUksRUFBRSxPQUFPLENBQUMsY0FBYztxQkFDN0I7aUJBQ0YsQ0FBQztnQkFDRixNQUFNLE1BQU0sR0FBRyx1QkFBdUIsQ0FBQyxLQUFLLEVBQUUsV0FBVyxDQUFDLENBQUM7Z0JBQzNELE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsV0FBVyxFQUFFLENBQUM7Z0JBQ3JDLE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLE1BQU0sQ0FBQyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQztnQkFDdEMsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsQ0FBQyxDQUFDLENBQUMsYUFBYSxDQUFDLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxDQUFDO2dCQUNuRCxNQUFNLENBQUMsTUFBTSxD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