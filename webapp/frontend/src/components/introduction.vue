<template>
  <div id="intro">
    <v-app>
      <v-content>
        <v-container fluid="true">
          <v-row justify="center">
            <h2>Location history analysis</h2>
          </v-row>
          <v-row justify="center" class="fill-height">
            <v-col cols="4">
              <v-card class="elevation-12">
                <v-toolbar color="primary" dark flat>
                  <v-spacer></v-spacer>
                  <v-toolbar-title>Please provide your email to continue</v-toolbar-title>
                  <v-spacer></v-spacer>
                </v-toolbar>
                <v-card-text>
                  <v-form onsubmit="return false" id="emailForm" @submit="validateEmail">
                    <v-text-field
                      id="email"
                      name="email"
                      v-model="email"
                      label="Email address"
                      prepend-icon="email"
                      type="text"
                    ></v-text-field>*After providing an email, we will ask you to upload a location history file. It can be downloaded from
                    <a
                      href="https://support.google.com/accounts/answer/3024190?hl=en"
                    >here.</a>
                  </v-form>
                  <v-dialog v-model="isEmailInvalid" max-width="400">
                    <v-card>
                      <v-card-title class="headline justify-center">InvalidEmail</v-card-title>
                      <v-card-text>The email is invalid. Please reenter it.</v-card-text>
                      <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="green" text @click="closeInvalidEmailPopUp">Try Again</v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-dialog>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" type="submit" form="emailForm">Continue</v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-content>
    </v-app>
  </div>
</template>

<script>
export default {
  name: "introduction",
  data: () => ({
    email: "",
    isEmailInvalid: false
  }),
  methods: {
    validateEmail(e) {
      console.log(this.email);
      var re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      this.isEmailInvalid = !re.test(String(this.email).toLowerCase());
      if (!this.isEmailInvalid) {
        this.$session.set("email", this.email);
        this.$router.push({ path: "upload" });
        // return true;
      }
      e.preventDefault();
    },
    closeInvalidEmailPopUp() {
      this.isEmailInvalid = false;
    }
  }
};
</script>