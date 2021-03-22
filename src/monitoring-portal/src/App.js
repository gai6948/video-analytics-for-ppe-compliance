import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import NorthStarThemeProvider from "aws-northstar/components/NorthStarThemeProvider";
import Amplify, { Auth } from "aws-amplify";
import AppLayout from "./components/AppLayout";
import AlarmTable  from "./components/AlarmTable";
import CameraView from "./components/CameraView";
import { AmplifyAuthenticator } from "@aws-amplify/ui-react";
import { useState, useEffect } from "react";
import { AuthState, onAuthUIStateChange } from "@aws-amplify/ui-components";

const settings = window.portalSettings || {};

Amplify.configure({
  Auth: {
    identityPoolId: settings.identityPoolId,
    region: settings.region,
    userPoolId: settings.userPoolId,
    userPoolWebClientId: settings.userPoolWebClientId,
  },
  aws_appsync_graphqlEndpoint: settings.graphqlEndpoint,
  aws_appsync_region: settings.region,
  aws_appsync_authenticationType: "AWS_IAM",
});

const withLayout = (Component) => (props) => (
  <AppLayout>
    <Component {...props} />
  </AppLayout>
);

const App = () => {
  const [authState, setAuthState] = useState();
  const [user, setUser] = useState();

  useEffect(() => {
    onAuthUIStateChange(async (nextAuthState, authData) => {
      setAuthState(nextAuthState);
      setUser(authData);
      // console.log(authData);
      const session = await Auth.currentSession();
      // console.log(session.getIdToken().getJwtToken());
    });
  }, []);


  return authState === AuthState.SignedIn && user ? (
    <NorthStarThemeProvider>
      <Router>
        <Switch>
          <Route
            exact
            path="/cameraview"
            component={withLayout(CameraView)}
          ></Route>
          <Route exact path="/" component={withLayout(AlarmTable)}></Route>
        </Switch>
      </Router>
    </NorthStarThemeProvider>
  ) : (
    <AmplifyAuthenticator />
  );
};

export default App;
