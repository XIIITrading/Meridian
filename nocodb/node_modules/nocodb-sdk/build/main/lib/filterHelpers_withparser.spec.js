"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const filterHelpers_old_spec_1 = require("./filterHelpers_old.spec");
const filterHelpers_withparser_1 = require("./filterHelpers_withparser");
const UITypes_1 = __importDefault(require("./UITypes"));
(0, filterHelpers_old_spec_1.testExtractFilterFromXwhere)('filterHelpers_withparser', filterHelpers_withparser_1.extractFilterFromXwhere);
describe('filterHelpers_withparser_specific', () => {
    describe('extractFilterFromXwhere', () => {
        describe('logical', () => {
            it('will parse basic logical query', () => {
                var _a;
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
                const result = (0, filterHelpers_withparser_1.extractFilterFromXwhere)(query, columnAlias);
                expect(result).toBeDefined();
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect((_a = result.filters[0].children) === null || _a === void 0 ? void 0 : _a[1].logical_op).toBe('and');
            });
            it('will parse nested logical query', () => {
                var _a;
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
                const result = (0, filterHelpers_withparser_1.extractFilterFromXwhere)(query, columnAlias);
                expect(result).toBeDefined();
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect((_a = result.filters[0].children) === null || _a === void 0 ? void 0 : _a[1].logical_op).toBe('or');
            });
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVyc193aXRocGFyc2VyLnNwZWMuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2ZpbHRlckhlbHBlcnNfd2l0aHBhcnNlci5zcGVjLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7O0FBQ0EscUVBQXVFO0FBQ3ZFLHlFQUFxRTtBQUNyRSx3REFBZ0M7QUFFaEMsSUFBQSxvREFBMkIsRUFDekIsMEJBQTBCLEVBQzFCLGtEQUF1QixDQUN4QixDQUFDO0FBRUYsUUFBUSxDQUFDLG1DQUFtQyxFQUFFLEdBQUcsRUFBRTtJQUNqRCxRQUFRLENBQUMseUJBQXlCLEVBQUUsR0FBRyxFQUFFO1FBQ3ZDLFFBQVEsQ0FBQyxTQUFTLEVBQUUsR0FBRyxFQUFFO1lBQ3ZCLEVBQUUsQ0FBQyxnQ0FBZ0MsRUFBRSxHQUFHLEVBQUU7O2dCQUN4QyxnREFBZ0Q7Z0JBQ2hELE1BQU0sS0FBSyxHQUFHLGdEQUFnRCxDQUFDO2dCQUMvRCxNQUFNLFdBQVcsR0FBK0I7b0JBQzlDLElBQUksRUFBRTt3QkFDSixFQUFFLEVBQUUsUUFBUTt3QkFDWixXQUFXLEVBQUUsTUFBTTt3QkFDbkIsS0FBSyxFQUFFLE1BQU07d0JBQ2IsSUFBSSxFQUFFLGlCQUFPLENBQUMsUUFBUTtxQkFDdkI7b0JBQ0QsSUFBSSxFQUFFO3dCQUNKLEVBQUUsRUFBRSxRQUFRO3dCQUNaLFdBQVcsRUFBRSxNQUFNO3dCQUNuQixLQUFLLEVBQUUsTUFBTTt3QkFDYixJQUFJLEVBQUUsaUJBQU8sQ0FBQyxjQUFjO3FCQUM3QjtpQkFDRixDQUFDO2dCQUVGLE1BQU0sTUFBTSxHQUFHLElBQUEsa0RBQXVCLEVBQUMsS0FBSyxFQUFFLFdBQVcsQ0FBQyxDQUFDO2dCQUMzRCxNQUFNLENBQUMsTUFBTSxDQUFDLENBQUMsV0FBVyxFQUFFLENBQUM7Z0JBQzdCLE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsV0FBVyxFQUFFLENBQUM7Z0JBQ3JDLE1BQU0sQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLE1BQU0sQ0FBQyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQztnQkFDdEMsTUFBTSxDQUFDLE1BQUEsTUFBTSxDQUFDLE9BQU8sQ0FBQyxDQUFDLENBQUMsQ0FBQyxRQUFRLDBDQUFHLENBQUMsRUFBRSxVQUFVLENBQUMsQ0FBQyxJQUFJLENBQUMsS0FBSyxDQUFDLENBQUM7WUFDakUsQ0FBQyxDQUFDLENBQUM7WUFDSCxFQUFFLENBQUMsaUNBQWlDLEVBQUUsR0FBRyxFQUFFOztnQkFDekMsZ0RBQWdEO2dCQUNoRCxNQUFNLEtBQUssR0FDVCxzRUFBc0UsQ0FBQztnQkFDekUsTUFBTSxXQUFXLEdBQStCO29CQUM5QyxJQUFJLEVBQUU7d0JBQ0osRUFBRSxFQUFFLFFBQVE7d0JBQ1osV0FBVyxFQUFFLE1BQU07d0JBQ25CLEtBQUssRUFBRSxNQUFNO3dCQUNiLElBQUksRUFBRSxpQkFBTyxDQUFDLFFBQVE7cUJBQ3ZCO29CQUNELElBQUksRUFBRTt3QkFDSixFQUFFLEVBQUUsUUFBUTt3QkFDWixXQUFXLEVBQUUsTUFBTTt3QkFDbkIsS0FBSyxFQUFFLE1BQU07d0JBQ2IsSUFBSSxFQUFFLGlCQUFPLENBQUMsY0FBYztxQkFDN0I7aUJBQ0YsQ0FBQztnQkFFRixNQUFNLE1BQU0sR0FBRyxJQUFBLGtEQUF1QixFQUFDLEtBQUssRUFBRSxXQUFXLENBQUMsQ0FBQztnQkFDM0QsTUFBTSxDQUFDLE1BQU0sQ0FBQyxDQUFDLFdBQVcsRUFBRSxDQUFDO2dCQUM3QixNQUFNLENBQUMsTUFBTSxDQUFDLE9BQU8sQ0FBQyxDQUFDLFdBQVcsRUFBRSxDQUFDO2dCQUNyQyxNQUFNLENBQUMsTUFBTSxDQUFDLE9BQU8sQ0FBQyxNQUFNLENBQUMsQ0FBQyxJQUFJLENBQUMsQ0FBQyxDQUFDLENBQUM7Z0JBQ3RDLE1BQU0sQ0FBQyxNQUFBLE1BQU0sQ0FBQyxPQUFPLENBQUMsQ0FBQyxDQUFDLENBQUMsUUFBUSwwQ0FBRyxDQUFDLEVBQUUsVUFBVSxDQUFDLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxDQUFDO1lBQ2hFLENBQUMsQ0FBQyxDQUFDO1FBQ0wsQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDIn0=