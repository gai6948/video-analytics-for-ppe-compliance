import React, { useCallback, useState, useEffect } from "react";
import { API, graphqlOperation } from "aws-amplify";
import Table from "aws-northstar/components/Table";
import StatusIndicator from "aws-northstar/components/StatusIndicator";
import Button from "aws-northstar/components/Button";
import Inline from "aws-northstar/layouts/Inline";
import ImageModal from "./ImageModal";
import { initialize } from "../utils/s3utils";

const listAlarms = ` query ListAlarm($count: Int, $nextToken: String) {
    listAlarm(count: $count, nextToken: $nextToken) {
      alarms {
        cameraId
        ts
        status
        s3url
        persons {
          id
        }
      }
      nextToken
    }
}`;

const AlarmTable = () => {
  const [loading, setLoading] = useState(false);
  const [alarmList, setAlarmList] = useState([]);
  const [nextToken, setNextToken] = useState("");
  const [s3, setS3] = useState(null);

  useEffect(() => {
    initialize().then((s3) => {
      setS3(s3);
    });
  }, []);

  const columnDefinitions = [
    {
      id: "status",
      width: 100,
      Header: "Status",
      accessor: "status",
      Cell: ({ row }) => {
        if (row && row.original) {
          const status = row.original.status;
          switch (status) {
            case "enabled":
              return (
                <StatusIndicator statusType="negative">Active</StatusIndicator>
              );
            case "disabled":
              return (
                <StatusIndicator statusType="positive">
                  Inactive
                </StatusIndicator>
              );
            default:
              return null;
          }
        }
        return row.id;
      },
    },
    {
      id: "cameraId",
      width: 200,
      Header: "Camera Id",
      accessor: "cameraId",
    },
    {
      id: "time",
      width: 200,
      Header: "Time",
      accessor: "time",
    },
    {
      id: "image",
      width: 100,
      Header: "Image",
      accessor: "s3url",
      Cell: ({ row }) => {
        if (row && row.original) {
          const s3key = row.original.s3url;
          return <ImageModal s3={s3} s3url={s3key} />;
        }
      },
    },
    {
      id: "noViolations",
      width: 100,
      Header: "No. of violations",
      accessor: "noViolations",
    },
  ];

  const tableActions = (
    <Inline>
      <Button variant="primary" onClick={() => alert("Dismiss button clicked")}>
        Dismiss
      </Button>
      <Button variant="normal" onClick={() => fetchNextAlarmList(25, nextToken)}>
        Next Page
      </Button>
    </Inline>
  );

  const handleAlarmData = (alarmsRes) => {
    const alarms = alarmsRes.data.listAlarm.alarms;
    setNextToken(alarmsRes.data.listAlarm.nextToken);
    const transformedAlarms = alarms.map((alm) => {
      const newAlarm = {};
      newAlarm.cameraId = alm.cameraId;
      const date = new Date(parseInt(alm.ts));
      newAlarm.time = date.toISOString();
      newAlarm.status = alm.status;
      newAlarm.noViolations = alm.persons.length;
      newAlarm.s3url = alm.s3url;
      return newAlarm;
    });
    setAlarmList(transformedAlarms);
    setLoading(false);
  };

  const fetchNextAlarmList = async (count = 25, nextToken) => {
    setLoading(true);
    try {
      const alarmsRes = await API.graphql(
        graphqlOperation(listAlarms, {
          count,
          nextToken,
        })
      );
      handleAlarmData(alarmsRes);
    } catch (error) {
      setLoading(false);
      console.error("Error fetching alarm from AppSync");
      console.error(error);
    }
  };

  const fetchAlarms = useCallback(async (options) => {
    setLoading(true);
    try {
      const alarmsRes =
        nextToken === ""
          ? await API.graphql(
              graphqlOperation(listAlarms, { count: options.pageSize })
            )
          : await API.graphql(
              graphqlOperation(listAlarms, {
                count: options.pageSize,
                nextToken,
              })
            );
        handleAlarmData(alarmsRes);
    } catch (error) {
      setLoading(false);
      console.error("Error fetching alarm from AppSync");
      console.error(error);
    }
  }, []);

  return (
    <Table
      actionGroup={tableActions}
      columnDefinitions={columnDefinitions}
      loading={loading}
      items={alarmList}
      disableFilters={true}
      pageSizes={[25]}
      errorText="Error fetching alarms from AppSync, try again later"
      onFetchData={fetchAlarms}
    />
  );
};

export default AlarmTable;
