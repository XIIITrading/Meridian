"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const MysqlUi_1 = require("./MysqlUi");
describe('MysqlUi', () => {
    describe('adjustLengthAndScale', () => {
        it('will set default length on new table and no scale', () => {
            const sqlUi = new MysqlUi_1.MysqlUi();
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
            const sqlUi = new MysqlUi_1.MysqlUi();
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
            const sqlUi = new MysqlUi_1.MysqlUi();
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiTXlzcWxVaS5zcGVjLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vLi4vc3JjL2xpYi9zcWxVaS9NeXNxbFVpLnNwZWMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7QUFBQSx1Q0FBb0M7QUFFcEMsUUFBUSxDQUFDLFNBQVMsRUFBRSxHQUFHLEVBQUU7SUFDdkIsUUFBUSxDQUFDLHNCQUFzQixFQUFFLEdBQUcsRUFBRTtRQUNwQyxFQUFFLENBQUMsbURBQW1ELEVBQUUsR0FBRyxFQUFFO1lBQzNELE1BQU0sS0FBSyxHQUFHLElBQUksaUJBQU8sRUFBRSxDQUFDO1lBQzVCLE1BQU0sU0FBUyxHQUFHO2dCQUNoQixFQUFFLEVBQUUsU0FBUztnQkFDYixJQUFJLEVBQUUsU0FBUztnQkFDZixJQUFJLEVBQUUsU0FBUzthQUNoQixDQUFDO1lBQ0YsS0FBSyxDQUFDLG9CQUFvQixDQUFDLFNBQVMsQ0FBQyxDQUFDO1lBQ3RDLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxDQUFDO1lBQ2hDLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ2pDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLDBDQUEwQyxFQUFFLEdBQUcsRUFBRTtZQUNsRCxNQUFNLEtBQUssR0FBRyxJQUFJLGlCQUFPLEVBQUUsQ0FBQztZQUM1QixNQUFNLFNBQVMsR0FBRztnQkFDaEIsRUFBRSxFQUFFLFNBQVM7Z0JBQ2IsSUFBSSxFQUFFLEdBQUc7Z0JBQ1QsSUFBSSxFQUFFLEVBQUU7YUFDVCxDQUFDO1lBQ0YsTUFBTSxTQUFTLEdBQUc7Z0JBQ2hCLEVBQUUsRUFBRSxTQUFTO2dCQUNiLElBQUksRUFBRSxTQUFTO2dCQUNmLElBQUksRUFBRSxTQUFTO2FBQ2hCLENBQUM7WUFDRixLQUFLLENBQUMsb0JBQW9CLENBQUMsU0FBUyxFQUFFLFNBQVMsQ0FBQyxDQUFDO1lBQ2pELE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxDQUFDO1lBQ2hDLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ2pDLENBQUMsQ0FBQyxDQUFDO1FBQ0gsRUFBRSxDQUFDLHVDQUF1QyxFQUFFLEdBQUcsRUFBRTtZQUMvQyxNQUFNLEtBQUssR0FBRyxJQUFJLGlCQUFPLEVBQUUsQ0FBQztZQUM1QixNQUFNLFNBQVMsR0FBRztnQkFDaEIsRUFBRSxFQUFFLFNBQVM7Z0JBQ2IsSUFBSSxFQUFFLEdBQUc7Z0JBQ1QsSUFBSSxFQUFFLEVBQUU7YUFDVCxDQUFDO1lBQ0YsTUFBTSxTQUFTLEdBQUc7Z0JBQ2hCLEVBQUUsRUFBRSxTQUFTO2dCQUNiLElBQUksRUFBRSxDQUFDO2dCQUNQLElBQUksRUFBRSxTQUFTO2FBQ2hCLENBQUM7WUFDRixLQUFLLENBQUMsb0JBQW9CLENBQUMsU0FBUyxFQUFFLFNBQVMsQ0FBQyxDQUFDO1lBQ2pELE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxDQUFDO1lBQ2hDLE1BQU0sQ0FBQyxTQUFTLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ2pDLENBQUMsQ0FBQyxDQUFDO0lBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyJ9