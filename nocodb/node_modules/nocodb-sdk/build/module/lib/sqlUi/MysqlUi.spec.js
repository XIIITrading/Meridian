import { MysqlUi } from './MysqlUi';
describe('MysqlUi', () => {
    describe('adjustLengthAndScale', () => {
        it('will set default length on new table and no scale', () => {
            const sqlUi = new MysqlUi();
            const newColumn = {
                dt: 'decimal',
                dtxs: undefined,
                dtxp: undefined,
            };
            sqlUi.adjustLengthAndScale(newColumn);
            expect(newColumn.dtxp).toBe(10);
            expect(newColumn.dtxs).toBe(2);
        });
        it('will set old column length with no scale', () => {
            const sqlUi = new MysqlUi();
            const oldColumn = {
                dt: 'decimal',
                dtxs: '2',
                dtxp: 11,
            };
            const newColumn = {
                dt: 'decimal',
                dtxs: undefined,
                dtxp: undefined,
            };
            sqlUi.adjustLengthAndScale(newColumn, oldColumn);
            expect(newColumn.dtxp).toBe(11);
            expect(newColumn.dtxs).toBe(2);
        });
        it('will set new column length with scale', () => {
            const sqlUi = new MysqlUi();
            const oldColumn = {
                dt: 'decimal',
                dtxs: '2',
                dtxp: 11,
            };
            const newColumn = {
                dt: 'decimal',
                dtxs: 5,
                dtxp: undefined,
            };
            sqlUi.adjustLengthAndScale(newColumn, oldColumn);
            expect(newColumn.dtxp).toBe(13);
            expect(newColumn.dtxs).toBe(5);
        });
    });
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiTXlzcWxVaS5zcGVjLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vLi4vc3JjL2xpYi9zcWxVaS9NeXNxbFVpLnNwZWMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsT0FBTyxFQUFFLE9BQU8sRUFBRSxNQUFNLFdBQVcsQ0FBQztBQUVwQyxRQUFRLENBQUMsU0FBUyxFQUFFLEdBQUcsRUFBRTtJQUN2QixRQUFRLENBQUMsc0JBQXNCLEVBQUUsR0FBRyxFQUFFO1FBQ3BDLEVBQUUsQ0FBQyxtREFBbUQsRUFBRSxHQUFHLEVBQUU7WUFDM0QsTUFBTSxLQUFLLEdBQUcsSUFBSSxPQUFPLEVBQUUsQ0FBQztZQUM1QixNQUFNLFNBQVMsR0FBRztnQkFDaEIsRUFBRSxFQUFFLFNBQVM7Z0JBQ2IsSUFBSSxFQUFFLFNBQVM7Z0JBQ2YsSUFBSSxFQUFFLFNBQVM7YUFDaEIsQ0FBQztZQUNGLEtBQUssQ0FBQyxvQkFBb0IsQ0FBQyxTQUFTLENBQUMsQ0FBQztZQUN0QyxNQUFNLENBQUMsU0FBUyxDQUFDLElBQUksQ0FBQyxDQUFDLElBQUksQ0FBQyxFQUFFLENBQUMsQ0FBQztZQUNoQyxNQUFNLENBQUMsU0FBUyxDQUFDLElBQUksQ0FBQyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUNqQyxDQUFDLENBQUMsQ0FBQztRQUNILEVBQUUsQ0FBQywwQ0FBMEMsRUFBRSxHQUFHLEVBQUU7WUFDbEQsTUFBTSxLQUFLLEdBQUcsSUFBSSxPQUFPLEVBQUUsQ0FBQztZQUM1QixNQUFNLFNBQVMsR0FBRztnQkFDaEIsRUFBRSxFQUFFLFNBQVM7Z0JBQ2IsSUFBSSxFQUFFLEdBQUc7Z0JBQ1QsSUFBSSxFQUFFLEVBQUU7YUFDVCxDQUFDO1lBQ0YsTUFBTSxTQUFTLEdBQUc7Z0JBQ2hCLEVBQUUsRUFBRSxTQUFTO2dCQUNiLElBQUksRUFBRSxTQUFTO2dCQUNmLElBQUksRUFBRSxTQUFTO2FBQ2hCLENBQUM7WUFDRixLQUFLLENBQUMsb0JBQW9CLENBQUMsU0FBUyxFQUFFLFNBQVMsQ0FBQyxDQUFDO1lBQ2pELE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxDQUFDO1lBQ2hDLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ2pDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLHVDQUF1QyxFQUFFLEdBQUcsRUFBRTtZQUMvQyxNQUFNLEtBQUssR0FBRyxJQUFJLE9BQU8sRUFBRSxDQUFDO1lBQzVCLE1BQU0sU0FBUyxHQUFHO2dCQUNoQixFQUFFLEVBQUUsU0FBUztnQkFDYixJQUFJLEVBQUUsR0FBRztnQkFDVCxJQUFJLEVBQUUsRUFBRTthQUNULENBQUM7WUFDRixNQUFNLFNBQVMsR0FBRztnQkFDaEIsRUFBRSxFQUFFLFNBQVM7Z0JBQ2IsSUFBSSxFQUFFLENBQUM7Z0JBQ1AsSUFBSSxFQUFFLFNBQVM7YUFDaEIsQ0FBQztZQUNGLEtBQUssQ0FBQyxvQkFBb0IsQ0FBQyxTQUFTLEVBQUUsU0FBUyxDQUFDLENBQUM7WUFDakQsTUFBTSxDQUFDLFNBQVMsQ0FBQyxJQUFJLENBQUMsQ0FBQyxJQUFJLENBQUMsRUFBRSxDQUFDLENBQUM7WUFDaEMsTUFBTSxDQUFDLFNBQVMsQ0FBQyxJQUFJLENBQUMsQ0FBQyxJQUFJLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDakMsQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDIn0=