import * as AppleAuthentication from 'expo-apple-authentication';
import { View, StyleSheet } from 'react-native';
import { supabase } from '../lib/supabase';

export default function AppleAuthButton() {
  return (
    <View style={styles.container}>
      <AppleAuthentication.AppleAuthenticationButton
        buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
        buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
        cornerRadius={5}
        style={styles.button}
        onPress={async () => {
          try {
            const credential = await AppleAuthentication.signInAsync({
              requestedScopes: [
                AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
                AppleAuthentication.AppleAuthenticationScope.EMAIL,
              ],
            });
            
            console.log('Apple Sign-In successful:', credential);
            
            // Sign in with Supabase using Apple identity token
            const { data, error } = await supabase.auth.signInWithIdToken({
              provider: 'apple',
              token: credential.identityToken!,
            });

            if (error) {
              console.error('Supabase sign-in error:', error);
            } else {
              console.log('Supabase sign-in successful:', data);
              
              // Update user profile with Apple data
              if (credential.fullName && data.user) {
                const { error: profileError } = await supabase
                  .from('profiles')
                  .upsert({
                    id: data.user.id,
                    full_name: `${credential.fullName.givenName} ${credential.fullName.familyName}`,
                    email: credential.email,
                  });
                
                if (profileError) {
                  console.error('Profile update error:', profileError);
                } else {
                  console.log('Profile updated successfully');
                }
              }
            }
            
          } catch (e: any) {
            if (e.code === 'ERR_REQUEST_CANCELED') {
              console.log('User canceled the sign-in flow');
            } else {
              console.error('Apple Sign-In error:', e);
            }
          }
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  button: {
    width: 200,
    height: 44,
  },
});