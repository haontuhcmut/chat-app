export interface AuthState {
    accessToken: string | null;
    user: User | null;
    loading: boolean;

    signUp: (username: string, password: string, confirm_password: string, email: string, fristName: string, lastName: string) => Promise<void>;
}