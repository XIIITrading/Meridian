"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SelectTypeConversionError = void 0;
const type_conversion_error_1 = require("./type-conversion.error");
class SelectTypeConversionError extends type_conversion_error_1.TypeConversionError {
    constructor(value, missingOptions) {
        super('');
        this.value = value;
        this.missingOptions = missingOptions;
        this.isErrorSuppressed = true;
    }
}
exports.SelectTypeConversionError = SelectTypeConversionError;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2VsZWN0LXR5cGUtY29udmVyc2lvbi5lcnJvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL3NyYy9saWIvZXJyb3Ivc2VsZWN0LXR5cGUtY29udmVyc2lvbi5lcnJvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFDQSxtRUFBOEQ7QUFFOUQsTUFBYSx5QkFDWCxTQUFRLDJDQUFtQjtJQUczQixZQUFxQixLQUFlLEVBQVcsY0FBd0I7UUFDckUsS0FBSyxDQUFDLEVBQUUsQ0FBQyxDQUFDO1FBRFMsVUFBSyxHQUFMLEtBQUssQ0FBVTtRQUFXLG1CQUFjLEdBQWQsY0FBYyxDQUFVO1FBRXJFLElBQUksQ0FBQyxpQkFBaUIsR0FBRyxJQUFJLENBQUM7SUFDaEMsQ0FBQztDQUdGO0FBVkQsOERBVUMifQ==