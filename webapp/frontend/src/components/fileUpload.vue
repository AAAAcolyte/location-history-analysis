<template>
  <div id="upload">
    <v-app>
      <v-content>
        <v-container fluid height="100%" class="is-fluid">
          <v-row justify="start">
            <v-col>
              <v-img max-width="10%" src="../assets/HumanDynamics.png"></v-img>
            </v-col>
          </v-row>
          <v-row justify="center">
            <v-col justify="center" cols="6">
              <v-card>
                <v-toolbar color="primary" dark flat>
                  <v-spacer></v-spacer>
                  <v-toolbar-title>Start by uploading a location history json file</v-toolbar-title>
                  <v-spacer></v-spacer>
                </v-toolbar>
                <v-card-text>
                  <v-form>
                    <v-file-input
                      @change="processJSON"
                      v-model="file"
                      ref="file"
                      accept=".json"
                      label="Choose a JSON file"
                      show-size
                    ></v-file-input>
                  </v-form>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" v-on:click="commitUpload" :loading="uploading">Continue</v-btn>
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
import { upload } from "../utils/upload-service";
export default {
  name: "upload",
  data: () => ({
    uploading: false
  }),
  methods: {
    processJSON() {},
    commitUpload() {
      this.uploading = true;
      upload(this.file)
        .then((response) => {
          this.uploading = false;
          console.log("SUCCESS!");
          console.log(response);
        })
        .catch(function(error) {
          console.log(error);
        });
    }
  }
};
</script>