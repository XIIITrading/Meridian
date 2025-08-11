import { testExtractFilterFromXwhere } from './filterHelpers_old.spec';
import { extractFilterFromXwhere } from './filterHelpers_withparser';
import UITypes from './UITypes';
testExtractFilterFromXwhere('filterHelpers_withparser', extractFilterFromXwhere);
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
                expect(result.filters).toBeDefined();
                expect(result.filters.length).toBe(1);
                expect((_a = result.filters[0].children) === null || _a === void 0 ? void 0 : _a[1].logical_op).toBe('or');
            });
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVyc193aXRocGFyc2VyLnNwZWMuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2ZpbHRlckhlbHBlcnNfd2l0aHBhcnNlci5zcGVjLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUNBLE9BQU8sRUFBRSwyQkFBMkIsRUFBRSxNQUFNLDBCQUEwQixDQUFDO0FBQ3ZFLE9BQU8sRUFBRSx1QkFBdUIsRUFBRSxNQUFNLDRCQUE0QixDQUFDO0FBQ3JFLE9BQU8sT0FBTyxNQUFNLFdBQVcsQ0FBQztBQUVoQywyQkFBMkIsQ0FDekIsMEJBQTBCLEVBQzFCLHVCQUF1QixDQUN4QixDQUFDO0FBRUYsUUFBUSxDQUFDLG1DQUFtQyxFQUFFLEdBQUcsRUFBRTtJQUNqRCxRQUFRLENBQUMseUJBQXlCLEVBQUUsR0FBRyxFQUFFO1FBQ3ZDLFFBQVEsQ0FBQyxTQUFTLEVBQUUsR0FBRyxFQUFFO1lBQ3ZCLEVBQUUsQ0FBQyxnQ0FBZ0MsRUFBRSxHQUFHLEVBQUU7O2dCQUN4QyxnREFBZ0Q7Z0JBQ2hELE1BQU0sS0FBSyxHQUFHLGdEQUFnRCxDQUFDO2dCQUMvRCxNQUFNLFdBQVcsR0FBK0I7b0JBQzlDLElBQUksRUFBRTt3QkFDSixFQUFFLEVBQUUsUUFBUTt3QkFDWixXQUFXLEVBQUUsTUFBTTt3QkFDbkIsS0FBSyxFQUFFLE1BQU07d0JBQ2IsSUFBSSxFQUFFLE9BQU8sQ0FBQyxRQUFRO3FCQUN2QjtvQkFDRCxJQUFJLEVBQUU7d0JBQ0osRUFBRSxFQUFFLFFBQVE7d0JBQ1osV0FBVyxFQUFFLE1BQU07d0JBQ25CLEtBQUssRUFBRSxNQUFNO3dCQUNiLElBQUksRUFBRSxPQUFPLENBQUMsY0FBYztxQkFDN0I7aUJBQ0YsQ0FBQztnQkFFRixNQUFNLE1BQU0sR0FBRyx1QkFBdUIsQ0FBQyxLQUFLLEVBQUUsV0FBVyxDQUFDLENBQUM7Z0JBQzNELE1BQU0sQ0FBQyxNQUFNLENBQUMsQ0FBQyxXQUFXLEVBQUUsQ0FBQztnQkFDN0IsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsQ0FBQyxXQUFXLEVBQUUsQ0FBQztnQkFDckMsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsTUFBTSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO2dCQUN0QyxNQUFNLENBQUMsTUFBQSxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsQ0FBQyxDQUFDLFFBQVEsMENBQUcsQ0FBQyxFQUFFLFVBQVUsQ0FBQyxDQUFDLElBQUksQ0FBQyxLQUFLLENBQUMsQ0FBQztZQUNqRSxDQUFDLENBQUMsQ0FBQztZQUNILEVBQUUsQ0FBQyxpQ0FBaUMsRUFBRSxHQUFHLEVBQUU7O2dCQUN6QyxnREFBZ0Q7Z0JBQ2hELE1BQU0sS0FBSyxHQUNULHNFQUFzRSxDQUFDO2dCQUN6RSxNQUFNLFdBQVcsR0FBK0I7b0JBQzlDLElBQUksRUFBRTt3QkFDSixFQUFFLEVBQUUsUUFBUTt3QkFDWixXQUFXLEVBQUUsTUFBTTt3QkFDbkIsS0FBSyxFQUFFLE1BQU07d0JBQ2IsSUFBSSxFQUFFLE9BQU8sQ0FBQyxRQUFRO3FCQUN2QjtvQkFDRCxJQUFJLEVBQUU7d0JBQ0osRUFBRSxFQUFFLFFBQVE7d0JBQ1osV0FBVyxFQUFFLE1BQU07d0JBQ25CLEtBQUssRUFBRSxNQUFNO3dCQUNiLElBQUksRUFBRSxPQUFPLENBQUMsY0FBYztxQkFDN0I7aUJBQ0YsQ0FBQztnQkFFRixNQUFNLE1BQU0sR0FBRyx1QkFBdUIsQ0FBQyxLQUFLLEVBQUUsV0FBVyxDQUFDLENBQUM7Z0JBQzNELE1BQU0sQ0FBQyxNQUFNLENBQUMsQ0FBQyxXQUFXLEVBQUUsQ0FBQztnQkFDN0IsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsQ0FBQyxXQUFXLEVBQUUsQ0FBQztnQkFDckMsTUFBTSxDQUFDLE1BQU0sQ0FBQyxPQUFPLENBQUMsTUFBTSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO2dCQUN0QyxNQUFNLENBQUMsTUFBQSxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsQ0FBQyxDQUFDLFFBQVEsMENBQUcsQ0FBQyxFQUFFLFVBQVUsQ0FBQyxDQUFDLElBQUksQ0FBQyxJQUFJLENBQUMsQ0FBQztZQUNoRSxDQUFDLENBQUMsQ0FBQztRQUNMLENBQUMsQ0FBQyxDQUFDO0lBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyJ9