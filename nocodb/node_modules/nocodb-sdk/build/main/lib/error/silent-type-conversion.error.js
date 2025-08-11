"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SilentTypeConversionError = void 0;
const type_conversion_error_1 = require("./type-conversion.error");
class SilentTypeConversionError extends type_conversion_error_1.TypeConversionError {
    constructor() {
        super('');
        this.isErrorSuppressed = true;
    }
}
exports.SilentTypeConversionError = SilentTypeConversionError;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2lsZW50LXR5cGUtY29udmVyc2lvbi5lcnJvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL3NyYy9saWIvZXJyb3Ivc2lsZW50LXR5cGUtY29udmVyc2lvbi5lcnJvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFDQSxtRUFBOEQ7QUFFOUQsTUFBYSx5QkFDWCxTQUFRLDJDQUFtQjtJQUczQjtRQUNFLEtBQUssQ0FBQyxFQUFFLENBQUMsQ0FBQztRQUNWLElBQUksQ0FBQyxpQkFBaUIsR0FBRyxJQUFJLENBQUM7SUFDaEMsQ0FBQztDQUdGO0FBVkQsOERBVUMifQ==