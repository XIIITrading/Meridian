/**
 * Determines if the exception is an expected control flow error.
 * - HttpException errors will have a status property
 * - RpcException errors will have an error property
 *
 * @returns `true` if the exception is expected and should not be reported to Sentry, otherwise `false`.
 */
export declare function isExpectedError(exception: unknown): boolean;
//# sourceMappingURL=helpers.d.ts.map